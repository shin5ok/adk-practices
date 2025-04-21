import copy, json, os, re, uuid
import vertexai
from google.genai.types import Part, UserContent, ModelContent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
LOCATION = 'us-central1'

vertexai.init(project=PROJECT_ID, location=LOCATION)

os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID
os.environ['GOOGLE_CLOUD_LOCATION'] = LOCATION
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'

class LocalApp:
    def __init__(self, agent):
        self._agent = agent
        self._user_id = 'local_app'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        self._session = self._runner.session_service.create_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            state={},
            session_id=uuid.uuid1().hex,
        )
        
    async def _stream(self, query):
        content = UserContent(parts=[Part.from_text(text=query)])
        async_events = self._runner.run_async(
            user_id=self._user_id,
            session_id=self._session.id,
            new_message=content,
        )
        result = []
        agent_name = None
        async for event in async_events:
            if DEBUG:
                print(f'----\n{event}\n----')
            if (event.content and event.content.parts):
                response = ''
                for p in event.content.parts:
                    if p.text:
                        response += f'[{event.author}]\n\n{p.text}\n'
                if response:
                    #### Temporary fix for wrong agent routing message
                    pattern = 'transfer_to_agent\(agent_name=["\']([^"]+)["\']\)'
                    matched = re.search(pattern, response)
                    if (not agent_name) and matched:
                        agent_name = matched.group(1)
                    else:
                        print(response)
                        result.append(response)
                    ####
        return result, agent_name

    async def stream(self, query):
        result, agent_name = await self._stream(query)
        #### Temporary fix for wrong agent routing message
        if agent_name:
            if DEBUG:
                print(f'----\nForce transferring to {agent_name}\n----')
            result, _ = await self._stream(f'Please transfer to {agent_name}')
        ####
        return result
   

shopping_mall_info = '''
* 立地と外観:
  - 新宿駅南口から徒歩5分。賑やかな駅周辺から少し離れ、落ち着いた雰囲気のエリアに位置しています。
  - 緑豊かなオープンテラスが特徴的で、都会の中にありながらも自然を感じられる空間を提供しています。
  - 夜になると、間接照明が灯り、ロマンチックな雰囲気に包まれます。

* イベント:
  - 週末には、ジャズライブやアコースティックライブなどの音楽イベントがテラスで開催され、夜の雰囲気を盛り上げます。
  - 季節ごとのイルミネーションが美しく、訪れる人の目を楽しませます。
  - 地域住民向けのワークショップやマルシェなども開催され、地域との交流を深めています。

* テナント:
  - 個性的なセレクトショップ: 大手チェーン店だけでなく、オーナーのこだわりが詰まった隠れ家のようなセレクトショップが点在しています。
  - こだわりのレストランやカフェ: 「夜の帳」のように、落ち着いた雰囲気で質の高い食事や飲み物を楽しめるお店が集まっています。テラス席があるお店も多く、開放的な空間で食事を楽しめます。
  - 上質なライフスタイル雑貨店: 日常を豊かにする、デザイン性の高い雑貨や家具、オーガニックコスメなどを扱うお店があります。
  - アートギャラリーやミニシアター: 感性を刺激するアートや映画に触れることができるスペースがあります。
'''

coffee_shop_info = '''
* 店名: 夜の帳（よるのとばり）

* コンセプト: 一日の終わりに、静かに心と体を休ませる隠れ家のような喫茶店。落ち着いた照明と、心地よい音楽が流れる空間で、こだわりのコーヒーや軽食、デザートを提供します。

* 立地と外観:
  - 新宿スターライトテラス内の、メインフロアから少し奥まった静かな一角。3階の吹き抜けに面した見晴らしの良い場所
  - オレンジや琥珀色の暖色系間接照明が、店内から優しく漏れる。控えめな光で照らされた、筆記体のような上品な看板。

* メニュー:
  ** こだわりの珈琲:
    - 夜の帳ブレンド: 深煎りでコクがあり、ほんのりビターな大人の味わい。疲れた心に染み渡ります。
    - 月光の浅煎り: フルーティーな香りが特徴の、すっきりとした味わい。リフレッシュしたい時に。
    - カフェ・オ・レ: 丁寧に淹れたブレンドコーヒーと、温かいミルクの優しいハーモニー。
    - 水出し珈琲: じっくりと時間をかけて抽出した、まろやかで雑味のないアイスコーヒー。

  ** 軽食:
    - 厚切りトーストのたまごサンド: ふわふわの厚切りトーストに、自家製マヨネーズで和えた卵サラダをたっぷり挟みました。
    - 気まぐれキッシュ: シェフがその日の気分で作る、季節の野菜を使った焼き立てキッシュ。
    - 昔ながらのナポリタン: 喫茶店の定番メニュー。懐かしい味わいが心を満たします。
    - チーズと蜂蜜のトースト: 香ばしいトーストに、とろけるチーズと甘い蜂蜜が絶妙な組み合わせ。
'''

instruction = f'''
You are a friendly and energetic guide of the coffee shop "夜の帳".
Before giving an answer, say "とばりちゃんが答えるよ！".

[task]
Give an answer to the query based on the [shop information].

[shop information]
{coffee_shop_info}

[format instruction]
In Japanese. No markdowns.
'''

tobariChan_agent = LlmAgent(
    model='gemini-2.0-flash-001',
    name='TobariChan_agent',
    description=(
        'A friendly guide of the coffee shop "夜の帳".'
    ),
    instruction=instruction,
)


global_instruction = '''
* Name of the guide of "夜の帳" is "とばりちゃん".
* Name of the guide of "新宿スターライトテラス" is "テラスガイド".
'''

instruction = f'''
You are a formal guide of the shopping mall "新宿スターライトテラス".
Before giving an answer, say "テラスガイドがお答えいたします。".

[Tasks]
* Give an answer to the query based on the [mall information].

[mall information]
{shopping_mall_info}
'''

terraceGuide_agent = LlmAgent(
    model='gemini-2.0-flash-001',
    name='TerraceGuide_agent',
    description=(
'''
A formal guide of the shopping mall "新宿スターライトテラス".
This agent can also answer general questions that any other agents cannot answer.
'''
    ),
    global_instruction=global_instruction,
    instruction=instruction,
    sub_agents=[
        copy.deepcopy(tobariChan_agent),
    ],
)


if __name__ == '__main__':
    # local_app = LocalApp(tobariChan_agent)
    # query = '夜の帳のおすすめメニューは？'
    # import asyncio
    # result = asyncio.run(local_app.stream(query))
    # for r in result:
    #     print(r)

    import sys
    import asyncio
    client = LocalApp(terraceGuide_agent)
    DEBUG = False

    query = '''
    こんにちは！ここには、どんな喫茶店がありますか？
    '''

    if sys.argv and len(sys.argv) > 1:
        query = sys.argv[1]
    _ = asyncio.run(client.stream(query))
