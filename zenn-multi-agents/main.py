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
    