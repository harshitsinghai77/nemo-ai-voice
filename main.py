import asyncio
import os
import argparse
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from prompts.prompt import base_prompt
import random
import json

from loguru import logger
import boto3
from pipecat.frames.frames import LLMRunFrame
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.aws.nova_sonic.llm import AWSNovaSonicLLMService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.aws.llm import AWSBedrockLLMContext
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.base_transport import TransportParams
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from strands import Agent
from strands.models import BedrockModel

from prompts.prompt import base_prompt, strands_system_prompt
from integration.confluence import get_confluence_page
from integration.github_utils import clone_github_repo
from integration.jira import create_jira_story
from custom_tools import file_read, journal, shell

load_dotenv(override=True)

# async def fetch_weather_from_api(params: FunctionCallParams):
#     print(f"==>> params: {params}")
#     temperature = 75 if params.arguments["format"] == "fahrenheit" else 24
#     await params.result_callback(
#         {
#             "conditions": "nice",
#             "temperature": temperature,
#             "format": params.arguments["format"],
#             "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
#         }
#     )


# weather_function = FunctionSchema(
#     name="get_current_weather",
#     description="Get the current weather",
#     properties={
#         "location": {
#             "type": "string",
#             "description": "The city and state, e.g. San Francisco, CA",
#         },
#         "format": {
#             "type": "string",
#             "enum": ["celsius", "fahrenheit"],
#             "description": "The temperature unit to use. Infer this from the users location.",
#         },
#     },
#     required=["location", "format"],
# )

# # Create tools schema
# tools = ToolsSchema(standard_tools=[weather_function])

session = boto3.Session(region_name="us-east-1")
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0", 
    boto_session=session,
)

async def run_bot(webrtc_connection):
    """Main bot entry point compatible with Pipecat Cloud."""

    strands_agent = Agent(
        name="StrandAgent",
        system_prompt=strands_system_prompt.format(project_name='nemo-ai'),
        model=bedrock_model,
        tools=[file_read, journal, shell, get_confluence_page, create_jira_story, clone_github_repo],
    )

    async def handle_strands_analysis(params: FunctionCallParams, query: str):
        """
        Perform technical exploration or context analysis using the Strands agent.

        This function delegates deep reasoning tasks (codebase analysis, documentation lookup,
        journaling) to the Strands agent. It allows Sonic to stay lightweight and conversational.

        Args:
            query (str): The user's request or question, e.g., "Check if our API supports OAuth."
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, strands_agent, query)
        await params.result_callback(result.message)


    pipecat_transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
            audio_out_10ms_chunks=2,
        ),
    )

    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-1'
    )

    stt = DeepgramSTTService(api_key=os.getenv('DEEPGRAM_API_KEY'))
    tts = CartesiaTTSService(
        api_key=os.getenv('CARTESIA_TTS_API_KEY'),
        voice_id="6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
    )

    llm = AWSBedrockLLMService(
        aws_region="us-east-1",
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        aws_access_key=session.get_credentials().access_key,
        aws_secret_key=session.get_credentials().secret_key,
    )
    
    # Initialize LLM service
    # llm = AWSNovaSonicLLMService(
    #     access_key_id=session.get_credentials().access_key,
    #     secret_access_key=session.get_credentials().secret_key,
    #     region='us-east-1',
    #     voice_id="tiffany",  # matthew, tiffany, amy
    # )

    # # Register function for function calls
    llm.register_direct_function(handle_strands_analysis)

    @llm.event_handler("on_function_calls_started")
    async def on_function_calls_started(service, function_calls):
        await tts.queue_frame(TTSSpeakFrame("Let me check on that."))

    tools = ToolsSchema(standard_tools=[handle_strands_analysis])

    # Set up context and context management.
    # system_instruction = (
    #     "You are a friendly assistant. The user and you will engage in a spoken dialog exchanging "
    #     "the transcripts of a natural real-time conversation. Keep your responses short, generally "
    #     "two or three sentences for chatty scenarios. "
    #     "Start by greeting the user."
    # )

    # sk_car_MEjs6Gzy4gL2SU2eDfumM9
    # deepgram - 64951bb20b01e4b496996699398611bac3164dca
 
    # context = AWSBedrockLLMContext(messages=[
    #         {"role": "system", "content": base_prompt},
    #         {"role": "user", "content": "Start by saying exactly this: 'Hi, I'm Lannister, and I'm here to help you plan your jira story'"},
    #     ],
    #     tools=tools,
    # )
    # context_aggregator = llm.create_context_aggregator(context)

    context = LLMContext(messages=[
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": "Start by saying exactly this: 'Hi, I'm Lannister, and I'm here to help you plan your jira story'"},
    ], tools=tools)
    context_aggregator = LLMContextAggregatorPair(context)    

    # Build the pipeline
    # pipeline = Pipeline(
    #     [
    #         pipecat_transport.input(),
    #         context_aggregator.user(),
    #         llm,
    #         pipecat_transport.output(),
    #         context_aggregator.assistant(),
    #     ]
    # )

    pipeline = Pipeline(
        [
            pipecat_transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            pipecat_transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Configure the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )
 
    @pipecat_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Pipecat Client connected")
        await task.queue_frames([LLMRunFrame()])
        # await llm.trigger_assistant_response()

    @pipecat_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)


# if __name__ == "__main__":
#     # Parse command line arguments for server configuration
#     asyncio.run(bot())


# scenario = json.dumps(random.choice(call_scenario_list))
# print(f"==>> scenario: {scenario}")
# tone_profile = json.dumps(random.choice(tone_profiles_list))
# print(f"==>> tone_profile: {tone_profile}")

# prompt = base_prompt.format(
#     name='Alex',
#     scenario=scenario,
#     tone_profile=tone_profile,
# )

# print("prompt", prompt)