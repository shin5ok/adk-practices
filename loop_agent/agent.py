from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

import sys

# --- Constants ---
APP_NAME = "doc_writing_app"
USER_ID = "dev_user_01"
SESSION_ID = "session_01"
GEMINI_MODEL = "gemini-2.0-flash"

# --- State Keys ---
STATE_INITIAL_TOPIC = "quantum physics"
STATE_INITIAL_TOPIC = "イタリア人をターゲットにした寿司レストランのキャッチコピー"
STATE_INITIAL_TOPIC = sys.argv[1] if len(sys.argv) > 1 else STATE_INITIAL_TOPIC
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
STATE_QUALITY_FEEDBACK = "quality_check" # 品質フィードバック用の新しいキーを追加

writer_agent = LlmAgent(
    name="WriterAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    あなたはクリエイティブライターAIです。
    セッションステートの `{STATE_CURRENT_DOC}` を確認してください。
    `{STATE_CURRENT_DOC}` が存在しないか空の場合、ステートキー `{STATE_INITIAL_TOPIC}` のトピックに基づいて非常に短い（1〜2文の）ストーリーまたはドキュメントを作成してください。
    `{STATE_CURRENT_DOC}` が*既に存在し*、`{STATE_CRITICISM}` がある場合、`{STATE_CRITICISM}` のコメントに従って `{STATE_CURRENT_DOC}` を修正してください。
    ストーリーまたは正確なパススルーメッセージ*のみ*を出力してください。
    """,
    description="最初のドキュメントの下書きを作成します。",
    output_key=STATE_CURRENT_DOC # 出力をステートに保存
)

# Critic Agent (LlmAgent)
critic_agent = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    あなたは建設的な批評家AIです。
    セッションステートキー `{STATE_CURRENT_DOC}` で提供されたドキュメントを確認してください。
    改善のための簡単な提案を1〜2つ提供してください（例：「もっとエキサイティングに」、「詳細を追加」「もっと人気が出るように」）。
    批評*のみ*を出力してください。
    """,
    description="現在のドキュメントの下書きをレビューします。",
    output_key=STATE_CRITICISM # 批評をステートに保存
)

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from typing import Optional
def quality_feedback(callback_context: CallbackContext) -> Optional[types.Content]:
    # import pprint;pprint.pprint(callback_context.user_content)
    # import pprint;pprint.pprint(callback_context.state.get(STATE_CURRENT_DOC))
    # import pprint;pprint.pprint(callback_context.state.to_dict())
    if n := callback_context.state.get(STATE_QUALITY_FEEDBACK):
        int_n = int(n)
        if int_n >= 8:
            print("品質フィードバック:", n)
            # https://google.github.io/adk-docs/callbacks/#the-callback-mechanism-interception-and-control
            return types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=STATE_CURRENT_DOC,
                    )
                ],
            )
    return None # process normally


# Quality Agent (LlmAgent)
quality_agent = LlmAgent(
    name="QualityAgent",
    model=GEMINI_MODEL,
    instruction=f"""
    あなたは品質評価AIです。
    わかりやすさの観点で、1-10の整数で現在のドキュメント{STATE_CURRENT_DOC}の品質を評価してください。
    整数*のみ*を出力してください（改行も不要）。
    """,
    after_agent_callback=quality_feedback,
    description="現在のドキュメントの品質を評価します。",
    output_key=STATE_QUALITY_FEEDBACK # 品質フィードバックをステートに保存
)



# Create the LoopAgent
loop_agent = LoopAgent(
    name="LoopAgent",
    sub_agents=[writer_agent, quality_agent, critic_agent], # quality_agent を2番目に追加
    max_iterations=5,
)

# Session and Runner
def call_agent(query, runner):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    n = 0
    for event in events:
        if event.is_final_response():
            n += 1
            final_response = event.content.parts[0].text
            print(f"{n} 回答者: {event.author}")
            print(final_response)
            print()


if __name__ == "__main__":

    session_service = InMemorySessionService()
    session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=loop_agent, app_name=APP_NAME, session_service=session_service)


    # Start the loop agent
    call_agent("execute", runner)

