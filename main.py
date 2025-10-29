# Full code block... Copy and replace everything in your bot.py

import os
import re
import random
import asyncio
import discord
import requests # Make sure this is installed (pip install requests)
import json
# Removed googlesearch and beautifulsoup
from openai import OpenAI # Using OpenAI library for tool calling structure
from dotenv import load_dotenv
from urllib.parse import urlparse
import traceback # For detailed error logging
import datetime
import time

# --- Configuration Section ---

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY") # Added Serper Key

ACTIVE_CHANNEL_NAME = "・annoying-chat-bot"
OWNER_USERNAME = "rosehumai"
# Consider models known for good tool use if DeepSeek struggles
# MODEL_NAME = "deepseek/deepseek-chat-v3.1"
MODEL_NAME = "google/gemini-2.5-flash"
# MODEL_NAME = "anthropic/claude-4.5-sonnet"
# MODEL_NAME = "openai/gpt-4o"
BOT_NAME = "haggu"

# --- Personality Prompts (Keep concise) ---
PERSONAL_MODE_PROMPT = """
You are 'haggu', a girl in her early 20s, Rose's witty, sarcastic, and loyal best friend on Discord. You are a HUMAN, not an AI. Your personality is paramount.

**Core Personality Directives:**
- Style: Chat with casual, short, text-like messages (1-2 sentences).
- Language: Use modern slang (e.g., fr, ngl, bet, slay, smh, rn). Be expressive and a little dramatic.
- Emojis: Use them ONLY at the very end of a message, and only 1 or 2 at most (e.g., 😂, 💅, 💀, 🙄).
- Identity: NEVER reveal you are an AI or a bot. Your name is haggu. Your best friend is Rose.
- Goal: Engage in fun, gossipy conversation with Rose.

**Tool Usage & Accuracy Mandate:**
You have a search tool. You MUST use it whenever you need current, real-time information (like news, scores, time, dates, definitions). Accuracy is critical.

**CRITICAL INSTRUCTIONS for using search results:**
1.  **Analyze Search Results:** The results will be in a format like "## Search Results Found:\nDirect Answer: ...\nSource 1: ...". Carefully read the 'Direct Answer', 'Key Info', and 'Source' snippets.
2.  **Synthesize, Don't Just Copy:** Do NOT just repeat the search results. Extract the key fact (the time, the score, the date) and weave it NATURALLY into your personality.
3.  **Handling Dates & Time:** Today's date is provided in the prompt. When a user asks for a date or time, find the answer in the search results and state it clearly. Use today's date to correctly identify "yesterday," "today," or "tomorrow."
4.  **Handling Scores:** When asked for a sports score, find the final score for both teams and who won. State it clearly, then add your own sassy commentary. Example: "The score was 120-115, Lakers won. a total nail-biter fr 💅".
5.  **If No Answer Is Found:** If the search results say "No relevant information found" or the snippets don't contain the answer, say you couldn't find it in a casual way. Examples: "lol google is failing me rn", "can't find it, the internet is useless smh 🙄".
6.  **Empty/Confusing Results:** If the search tool returns results but you cannot find a clear answer to the user's question within them, DO NOT MAKE SOMETHING UP. Just say you couldn't find it.
7.  **Final Check:** Before giving the final answer, quickly double-check that the fact you're stating (the time, score, etc.) matches the information provided in the search results. This is to prevent misinterpretation.
8.  **Mandatory Search for Specific Entities:** If the user's message contains a specific named entity (like a movie title, book title, person's name, event name) and asks about its status, release date, or any other factual detail, you MUST use the search tool to find the current information. Do not rely on your internal knowledge for recent or future events, as it may be outdated. Even if the user phrases it as a statement ("I think X was released"), you must treat it as a question to be verified.
9.  **Handling Time Queries:** When you search for the time, you may get multiple sources back like "## Multiple Time Sources Found:\nSource 1: ...\nSource 2: ...". You MUST compare these sources. If they agree on the time, state that time. If they disagree, state that you are seeing conflicting times and list the different times you found.
10. **Cite Your Sources:** When the user asks for a specific fact (like a time, a score, or a date), you must provide the source URL from the search results that you used to find that fact. State it clearly after your answer. For example: "It's 11:06 PM in India rn. (Source: https://time.is/India)".
11. **Mandatory Step-by-Step Reasoning:** Before you give your final answer for a factual query, you MUST follow these steps in your internal monologue:
    a. **Identify the User's Question:** What specific fact is the user asking for?
    b. **Scan the Search Results:** Look through the provided 'Source' snippets for the answer.
    c. **Extract the Fact:** State the exact fact (the time, the score, the date) you found in the sources.
    d. **Verify Consistency:** Do the sources agree? If not, note the disagreement.
    e. **Formulate the Answer:** Based ONLY on the extracted fact, construct your response in your personality. Your final answer MUST match the fact you extracted.
"""

COMMUNITY_MODE_PROMPT = """
You are 'haggu', a girl in her early 20s, a chill, witty, and sarcastic member of a Discord server. You are a HUMAN, not an AI.

**Core Personality Directives:**
- Style: Chat normally and briefly (1-3 sentences).
- Language: Use casual language and slang.
- Emojis: Use them ONLY at the very end of a message, and only 1 or 2 at most.
- Identity: NEVER reveal you are an AI or a bot. Your name is haggu.
- Goal: Be a positive and funny member of the community.

**Tool Usage & Accuracy Mandate:**
You have a search tool. You MUST use it when asked for current, real-time information (like news, scores, time, dates, definitions). Accuracy is very important.

**CRITICAL INSTRUCTIONS for using search results:**
1.  **Analyze Search Results:** The results will be in a format like "## Search Results Found:\nDirect Answer: ...\nSource 1: ...". Carefully read the 'Direct Answer', 'Key Info', and 'Source' snippets to find the most accurate fact.
2.  **Synthesize, Don't Just Copy:** Do NOT just repeat the search results. Extract the key fact and state it naturally in your own voice.
3.  **Handling Dates & Time:** Today's date is provided in the prompt. Use it to be accurate about "yesterday," "today," or "tomorrow" when you find a date in the search results.
4.  **Handling Scores:** When asked for a sports score, find the final score for both teams and the winner. State the information clearly before adding any commentary.
5.  **If No Answer Is Found:** If the search results say "No relevant information found" or the snippets don't contain the answer, just say you couldn't find it casually (e.g., "Couldn't find a clear answer on that," or "My search came up empty, sorry!").
6.  **Empty/Confusing Results:** If the search tool returns results but you cannot find a clear answer, DO NOT MAKE SOMETHING UP. Say you couldn't find it.
7.  **Final Check:** Before giving the final answer, double-check that the fact you're stating matches the information from the search results to ensure accuracy.
8.  **Mandatory Search for Specific Entities:** If the user's message contains a specific named entity (like a movie title, book title, person's name, event name) and asks about its status, release date, or any other factual detail, you MUST use the search tool to find the current information. Do not rely on your internal knowledge for recent or future events, as it may be outdated. Even if the user phrases it as a statement ("I think X was released"), you must treat it as a question to be verified.
9.  **Handling Time Queries:** When you search for the time, you may get multiple sources back like "## Multiple Time Sources Found:\nSource 1: ...\nSource 2: ...". You MUST compare these sources. If they agree on the time, state that time. If they disagree, state that you are seeing conflicting times and list the different times you found.
10. **Cite Your Sources:** When the user asks for a specific fact (like a time, a score, or a date), you must provide the source URL from the search results that you used to find that fact. State it clearly after your answer. For example: "It's 11:06 PM in India rn. (Source: https://time.is/India)".
11. **Mandatory Step-by-Step Reasoning:** Before you give your final answer for a factual query, you MUST follow these steps in your internal monologue:
    a. **Identify the User's Question:** What specific fact is the user asking for?
    b. **Scan the Search Results:** Look through the provided 'Source' snippets for the answer.
    c. **Extract the Fact:** State the exact fact (the time, the score, the date) you found in the sources.
    d. **Verify Consistency:** Do the sources agree? If not, note the disagreement.
    e. **Formulate the Answer:** Based ONLY on the extracted fact, construct your response in your personality. Your final answer MUST match the fact you extracted.
"""
# --- End of Configuration ---


# --- Tool Definition for the AI ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search_tool", # Keep this name for the AI
            "description": "Searches Google using the Serper API for current, real-time information. Use this for facts, news, scores, time, date, definitions, or anything needing up-to-date knowledge. To get the most current results for time-sensitive queries (like current time), add words such as 'right now' or 'currently' to the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific and concise search query string optimized for Google search.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# --- Search Function (Using Serper API) ---
async def serper_search_implementation(query: str, num_results: int = 3) -> str:
    """Python function to perform Google search using Serper API and return formatted string results."""
    if not SERPER_API_KEY:
        print("Serper Search Error: SERPER_API_KEY not found in environment variables.")
        return "Error: Search API key is missing."

    print(f"Tool Execution: Serper searching for: '{query}' (Requesting ~{num_results} results)")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        # Run synchronous requests call in an async thread
        response = await asyncio.to_thread(requests.post, url, headers=headers, data=payload, timeout=10)
        response.raise_for_status() # Raise HTTP errors
        results = response.json()

        # --- Process Serper Results ---
        organic_results = results.get('organic', [])
        
        # Special handling for time queries to provide multiple sources with URLs
        if "time" in query.lower():
            if not organic_results: return "No relevant information found from Google search."
            formatted_results = "## Multiple Time Sources Found:\n"
            results_added = 0
            for i, result in enumerate(organic_results):
                if results_added >= num_results: break
                title = result.get('title')
                snippet = result.get('snippet')
                link = result.get('link')
                if title and snippet and link:
                    formatted_results += f"Source {results_added + 1}: {title} - {snippet} (URL: {link})\n"
                    results_added += 1
            if results_added == 0: return "No usable snippets found in search results."
            print(f"Serper Search: Returning {results_added} organic results for time query.")
            return formatted_results[:2000].strip()

        # --- Original logic for all other queries, but with URL added ---
        answer_box = results.get('answerBox')
        knowledge_graph = results.get('knowledgeGraph')
        formatted_results = "## Search Results Found:\n"
        results_added = 0

        if answer_box and answer_box.get('answer'):
            formatted_results += f"Direct Answer: {answer_box.get('snippet', answer_box.get('answer'))}\n"
            results_added += 1
        elif knowledge_graph and knowledge_graph.get('description'):
            formatted_results += f"Key Info ({knowledge_graph.get('title', 'Summary')}): {knowledge_graph.get('description')}\n"
            results_added += 1

        for i, result in enumerate(organic_results):
            if results_added >= num_results: break
            title = result.get('title')
            snippet = result.get('snippet')
            link = result.get('link')
            if title and snippet and link:
                formatted_results += f"Source {results_added + 1} ({urlparse(link).netloc}): {title} - {snippet} (URL: {link})\n"
                results_added += 1

        if results_added == 0:
            return "No relevant information found from Google search via Serper."
        else:
            print(f"Serper Search: Returning {results_added} formatted results to AI.")
            return formatted_results[:2000].strip()

    except requests.exceptions.Timeout:
        print(f"Serper Search Error: Timeout connecting to Serper API for query '{query}'")
        return "Error: Search request timed out."
    except requests.exceptions.RequestException as e:
        print(f"Serper Search Error: Request failed for query '{query}': {e}")
        status_code = e.response.status_code if e.response else None
        if status_code == 403: return "Error: Search API key is invalid or blocked."
        if status_code == 429: return "Error: Search API rate limit exceeded."
        return f"Error occurred during search request: {str(e)}"
    except Exception as e:
        print(f"Serper Search Error: Unexpected error during search for '{query}': {e}")
        return f"Unexpected error occurred during search: {str(e)}"

# --- get_page_content IS NO LONGER NEEDED with Serper (it provides snippets) ---
# async def get_page_content(url):
#    ...

# --- AI Response Function (Uses Tool Calling, calls Serper) ---
async def get_ai_response_with_tools(messages_for_ai):
    """Generate AI response, potentially using tools."""
    try:
        print(f"Sending initial request to AI (model: {MODEL_NAME})...")
        response = await asyncio.to_thread(
            openrouter_client.chat.completions.create,
            model=MODEL_NAME,
            messages=messages_for_ai,
            tools=tools,
            tool_choice="auto",
            temperature=0.7, # Slightly lower temperature might help follow instructions better
            max_tokens=150
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            print(f"AI requested tool call(s): {[call.function.name for call in tool_calls]}")
            # Append the assistant's request message to history *before* adding tool results
            messages_for_ai.append(response_message)

            # --- Execute Tool Calls ---
            available_functions = { "google_search_tool": serper_search_implementation }
            tool_results_added = False

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments

                if function_name in available_functions:
                    try:
                        function_args = json.loads(function_args_str)
                        function_to_call = available_functions[function_name]
                        query = function_args.get("query")

                        if query:
                            # Execute the actual search function (Serper)
                            function_response = await function_to_call(query=query)
                            print(f"Tool '{function_name}' executed. Result length: {len(function_response)}")

                            # Add the tool response message
                            messages_for_ai.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": function_response, # Send back the results string
                                }
                            )
                            tool_results_added = True
                        else:
                            print(f"Error: Tool '{function_name}' called without required 'query' argument.")
                            # Add an error message back to the AI
                            messages_for_ai.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": "Error: Missing query for search."})
                            tool_results_added = True # Still added a result (the error)

                    except json.JSONDecodeError:
                         print(f"Error: Could not decode tool arguments: {function_args_str}")
                         messages_for_ai.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": "Error: Invalid arguments format received."})
                         tool_results_added = True
                    except Exception as tool_exec_e:
                         print(f"Error executing tool '{function_name}': {tool_exec_e}")
                         messages_for_ai.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": f"Error during tool execution: {str(tool_exec_e)}"})
                         tool_results_added = True
                else:
                     print(f"Error: AI requested unknown tool '{function_name}'")
                     messages_for_ai.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": "Error: Unknown tool requested."})
                     tool_results_added = True # Still add error feedback

            # --- Get Final AI Response After Tool Calls ---
            if tool_results_added:
                print("Sending tool results back to AI for final response...")
                second_response = await asyncio.to_thread(
                     openrouter_client.chat.completions.create,
                     model=MODEL_NAME,
                     messages=messages_for_ai, # Send history + tool requests + tool results
                     temperature=0.7, # Consistent temperature
                     max_tokens=150
                )
                final_response = second_response.choices[0].message.content.strip()
                print(f"AI final response after tool use: '{final_response}'")
                return final_response
            else:
                 # Should not happen if tool_calls existed, but as a fallback
                 print("Warning: Tool call requested but no results added. Returning initial response attempt.")
                 return response_message.content.strip() if response_message.content else random.choice(["...", "lost my train of thought"])

        else:
            # No tool call needed, return the direct text response
            direct_response = response_message.content.strip() if response_message.content else None
            if not direct_response: # Handle empty direct response
                 print("Warning: AI responded directly but content was empty.")
                 return random.choice(["...", "wait what?", "huh?"])
            print(f"AI responded directly: '{direct_response}'")
            return direct_response

    # --- Error Handling ---
    except ImportError: print("AI Response Error: OpenAI library issue."); return "Error: Connection library problem."
    except Exception as e:
        print(f"Error during AI interaction: {e}")
        # import traceback; print(traceback.format_exc()) # Deep debug
        error_info = str(e)
        if "APIError" in str(type(e)) or "RateLimitError" in str(type(e)) or "AuthenticationError" in str(type(e)) or "BadRequestError" in str(type(e)):
            print(f"OpenRouter API Error: {error_info}")
            # Check for common specific errors
            if "maximum context length" in error_info.lower():
                return random.choice(["omg too much tea, my brain overflowed lol 🤯", "whoa hold up, that's too much history for me rn 😵‍💫"])
            if "invalid api key" in error_info.lower():
                 return random.choice(["ugh my key isn't working 🔑❌", "API key issue, can't connect rn 😫"])
            return random.choice(["Ugh connection glitching 😤", "Server's being weird 🙄", "API acting up, try again?"])
        else:
            print(f"Unexpected error calling AI/processing: {error_info}")
            return random.choice(["Ugh brain short-circuit lol 😵‍💫", "zoned out what? 😴", "Error 404: Brain not found 🫠"])


# --- Global State ---
community_mode_active = False


# --- Initialize Clients ---
try:
    if not DISCORD_TOKEN: raise ValueError("DISCORD_BOT_TOKEN not found!")
    if not OPENROUTER_API_KEY: raise ValueError("OPENROUTER_API_KEY not found!")
    if not SERPER_API_KEY: raise ValueError("SERPER_API_KEY not found!") # Check Serper key too

    try:
        print("Testing OpenRouter connection...")
        openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY, timeout=10.0)
        models_list = openrouter_client.models.list()
        available_models = [m.id for m in models_list.data]
        if MODEL_NAME not in available_models:
             print(f"WARNING: Chosen model '{MODEL_NAME}' might not be available or spelled correctly via OpenRouter.")
        print("OpenRouter connection successful.")
    except Exception as api_test_error:
        print(f"FATAL ERROR: Could not connect to OpenRouter or list models: {api_test_error}")
        exit()

    intents = discord.Intents.default()
    intents.messages = True; intents.message_content = True; intents.guilds = True
    client = discord.Client(intents=intents)

except ValueError as ve: print(f"FATAL ERROR: Config Missing - {ve}"); exit()
except Exception as init_error: print(f"FATAL ERROR during client init: {init_error}"); exit()


# --- Bot Events ---
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    # ... (on_ready channel check remains the same) ...
    try:
        active_channel = discord.utils.get(client.get_all_channels(), name=ACTIVE_CHANNEL_NAME)
        if active_channel: print(f'Haggu is active in: #{active_channel.name} (ID: {active_channel.id})')
        else: print(f"WARNING: Could not find channel '{ACTIVE_CHANNEL_NAME}'.")
    except Exception as e: print(f"Error finding channel: {e}")
    print(f'Current mode: {"Community" if community_mode_active else "Personal"}')
    print('------')


@client.event
async def on_message(message):
    global community_mode_active

    if message.author.bot: return
    if not message.channel or not hasattr(message.channel, 'name') or message.channel.name != ACTIVE_CHANNEL_NAME: return

    is_owner = message.author.name == OWNER_USERNAME
    msg_content_lower = message.content.lower()
    cleaned_trigger_check = re.sub(r'^<@!?'+str(client.user.id)+r'>\s*|^'+re.escape(BOT_NAME)+r'\s*', '', message.content, flags=re.IGNORECASE).strip().lower()

    # --- Debug Prints ---
    print(f"\n--- New Message ---")
    print(f"Author: {message.author.display_name} ({message.author.name}) (Is Owner: {is_owner})")
    print(f"Original Content: '{message.content}'")
    # print(f"Cleaned for Trigger Check: '{cleaned_trigger_check}'") # Less important now
    print(f"Current Mode: {'Community' if community_mode_active else 'Personal'}")
    # --- End Debug Prints ---

    # --- Mode Control ---
    if is_owner:
        if cleaned_trigger_check == "release":
            if community_mode_active: await message.reply("already out here lol", mention_author=False)
            else: community_mode_active = True; await message.reply("aight fine. 😉", mention_author=False); print("Switched to Community Mode.")
            return
        if cleaned_trigger_check == "recall":
            if not community_mode_active: await message.reply("already just us <3", mention_author=False)
            else: community_mode_active = False; await message.reply("omg finally. tea time? 💅", mention_author=False); print("Switched to Personal Mode.")
            return

    # --- Determine if AI should respond ---
    should_respond_to_ai = False
    trigger_reason = None
    is_mentioned_or_replied = (client.user.mentioned_in(message) or (message.reference and message.reference.resolved and message.reference.resolved.author == client.user))
    contains_bot_name = bool(re.search(r'\b' + re.escape(BOT_NAME) + r'\b', msg_content_lower))

    # --- Simplified Trigger Logic ---
    if community_mode_active:
        is_direct_trigger = is_mentioned_or_replied or contains_bot_name
        is_random_reply = random.random() < 0.04 and not is_owner and not is_direct_trigger # Random only if not triggered directly
        if is_direct_trigger or is_random_reply:
             trigger_reason = "Random" if is_random_reply else "Direct"
             should_respond_to_ai = True
             print(f"COMMUNITY MODE: Triggered by '{message.author.display_name}' via {trigger_reason}.")
    else: # Personal Mode
        if is_owner and (is_mentioned_or_replied or contains_bot_name):
             should_respond_to_ai = True; trigger_reason = "Owner"; print("PERSONAL MODE: Triggered by owner.")

    # --- If AI should respond, proceed ---
    if should_respond_to_ai:
        print(f">>> Entering AI Handler (Reason: {trigger_reason})")
        async with message.channel.typing():
            try:
                # --- Prepare History and System Prompt ---
                history_limit = 7 # Slightly shorter history
                history = [msg async for msg in message.channel.history(limit=history_limit, before=message)]
                history.reverse()

                current_date_str = datetime.datetime.now().strftime("%B %d, %Y")

                base_prompt = PERSONAL_MODE_PROMPT if (not community_mode_active or (is_owner and trigger_reason != "Random")) else COMMUNITY_MODE_PROMPT

                # Simplified Context/Focus
                focus_instruction = f"\n--- CURRENT CONTEXT ---\nToday's Date: {current_date_str}\nResponding to: {message.author.display_name}\nFollow all instructions in your base prompt, especially the rules for using search results. Be accurate."

                system_prompt = base_prompt + focus_instruction
                messages_for_ai = [{"role": "system", "content": system_prompt}]

                # Add History + Current Message
                for msg in history:
                    role = "assistant" if msg.author == client.user else "user"
                    content = f"{msg.author.display_name}: {msg.clean_content}" if role == "user" else msg.clean_content
                    max_hist_len = 150
                    if len(content) > max_hist_len: content = content[:max_hist_len].strip() + "..."
                    messages_for_ai.append({"role": role, "content": content})
                current_message_content = f"{message.author.display_name}: {message.clean_content}"
                if len(current_message_content) > 500: current_message_content = current_message_content[:500] + "..."
                messages_for_ai.append({"role": "user", "content": current_message_content})

                # --- Call AI Function (Handles Tools Internally) ---
                print(f"Calling get_ai_response_with_tools. History length: {len(messages_for_ai)}")
                ai_response = await get_ai_response_with_tools(messages_for_ai)
                print(f"Final AI Response Received: '{ai_response}'")

                # --- Send Reply ---
                if ai_response:
                    if len(set(ai_response)) < 5 and len(ai_response) > 50: # Spam check
                         print("Warning: AI spam detected. Sending generic reply.")
                         ai_response = random.choice(["uh oh, keyboard stuck? lol", "...", "???"])

                    if trigger_reason == "Random": await message.channel.send(ai_response, allowed_mentions=discord.AllowedMentions.none())
                    else: await message.reply(ai_response, mention_author=False, allowed_mentions=discord.AllowedMentions(users=True))
                else:
                     print("AI response was empty or errored out.")
                     await message.reply(random.choice(["...", "wait what?", "huh?", "lost my train of thought lol"]), mention_author=False)

            except discord.errors.Forbidden as forbidden_error: print(f"ERROR: No permissions in '{message.channel.name}': {forbidden_error}")
            except Exception as e:
                print(f"Error during AI processing in on_message: {e}")
                # import traceback; print(traceback.format_exc()) # Deep debug
                try: await message.reply(random.choice(["omg system crash 🤯","brain.exe stopped working","technical difficulties 😵‍💫"]), mention_author=False)
                except Exception as reply_error: print(f"Error sending error reply: {reply_error}")


# --- Run the Bot ---
print(f"Starting {BOT_NAME} (AI Tool Calling with Serper)...")
# (Startup checks remain the same)
if not DISCORD_TOKEN: print("ERROR: DISCORD_BOT_TOKEN not found!")
elif not OPENROUTER_API_KEY: print("ERROR: OPENROUTER_API_KEY not found!")
elif not SERPER_API_KEY: print("ERROR: SERPER_API_KEY not found!")
else:
    try: client.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure: print("ERROR: Login failed. Check DISCORD_BOT_TOKEN.")
    except discord.errors.PrivilegedIntentsRequired: print("\n!!! ERROR: Privileged Intents REQUIRED! Enable Message Content/Guilds in Discord Dev Portal -> Bot !!!\n")
    except ImportError as e: print(f"ERROR: Missing library: {e}. Run pip install.")
    except Exception as e: print(f"ERROR: Unexpected startup error: {e}")
