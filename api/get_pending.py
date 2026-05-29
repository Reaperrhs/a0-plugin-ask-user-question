from helpers.api import ApiHandler, Request
from usr.plugins.ask_user_question.helpers.state import get_pending


class GetPending(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ['GET', 'POST']

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict:
        context_id = input.get('context_id', '') or request.args.get('context_id', '')

        if not context_id:
            return {'ok': False, 'error': 'Missing context_id'}

        session = get_pending(context_id)

        if session is None or session.result is not None:
            return {'ok': True, 'pending': False}

        questions_data = []
        for q in session.questions:
            opts = []
            for o in q.options:
                opt_data = {'label': o.label, 'description': o.description}
                if o.preview:
                    opt_data['preview'] = o.preview
                opts.append(opt_data)

            questions_data.append({
                'question': q.question,
                'header': q.header,
                'options': opts,
                'multiSelect': q.multi_select,
            })

        return {
            'ok': True,
            'pending': True,
            'session_id': session.session_id,
            'questions': questions_data,
            'created_at': session.created_at,
        }
