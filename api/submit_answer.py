from helpers.api import ApiHandler, Request
from usr.plugins.ask_user_question.helpers.state import submit_answer


class SubmitAnswer(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ['POST']

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict:
        session_id = input.get('session_id', '')
        answers = input.get('answers', [])
        cancelled = input.get('cancelled', False)

        if not session_id:
            return {'ok': False, 'error': 'Missing session_id'}

        if not cancelled and not answers:
            return {'ok': False, 'error': 'Missing answers'}

        session = submit_answer(session_id, answers, cancelled)

        if session is None:
            return {'ok': False, 'error': 'Session not found'}

        return {'ok': True}
