from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from helpers.tool import Tool, Response
from agent import AgentContext
from helpers.notification import NotificationPriority, NotificationType

from usr.plugins.ask_user_question.helpers.state import (
    create_session,
    cleanup_old_sessions,
    get_pending,
)

RESERVED_LABELS = {'Other', 'Type something.', 'Chat about this', 'Next →'}


class AskUserQuestion(Tool):

    async def execute(self, **kwargs) -> Response:
        cleanup_old_sessions()

        questions_raw = self.args.get('questions', [])
        timeout = int(self.args.get('timeout', 300))

        if not questions_raw or not isinstance(questions_raw, list):
            return Response(
                message='Error: questions must be a non-empty array.',
                break_loop=False,
            )

        if len(questions_raw) < 1 or len(questions_raw) > 4:
            return Response(
                message='Error: Must provide 1-4 questions.',
                break_loop=False,
            )

        for i, q in enumerate(questions_raw):
            if not isinstance(q, dict):
                return Response(
                    message=f'Error: Question {i+1} must be an object.',
                    break_loop=False,
                )

            question_text = str(q.get('question', '')).strip()
            if not question_text:
                return Response(
                    message=f'Error: Question {i+1} is missing question text.',
                    break_loop=False,
                )
            if not question_text.endswith('?'):
                return Response(
                    message=f'Error: Question {i+1} text must end with ?',
                    break_loop=False,
                )

            header = str(q.get('header', '')).strip()
            if not header:
                return Response(
                    message=f'Error: Question {i+1} is missing header.',
                    break_loop=False,
                )
            if len(header) > 16:
                return Response(
                    message=f'Error: Question {i+1} header must be max 16 characters (got {len(header)}).',
                    break_loop=False,
                )

            options = q.get('options', [])
            if not isinstance(options, list) or len(options) < 2 or len(options) > 4:
                return Response(
                    message=f'Error: Question {i+1} must have 2-4 options.',
                    break_loop=False,
                )

            for j, opt in enumerate(options):
                if not isinstance(opt, dict):
                    return Response(
                        message=f'Error: Question {i+1} option {j+1} must be an object.',
                        break_loop=False,
                    )
                label = str(opt.get('label', '')).strip()
                if not label:
                    return Response(
                        message=f'Error: Question {i+1} option {j+1} missing label.',
                        break_loop=False,
                    )
                if len(label) > 60:
                    return Response(
                        message=f'Error: Question {i+1} option {j+1} label must be max 60 characters.',
                        break_loop=False,
                    )
                if label in RESERVED_LABELS:
                    return Response(
                        message=f'Error: Question {i+1} option {j+1} uses reserved label: {label}',
                        break_loop=False,
                    )

        context_id = self.agent.context.id if self.agent.context else ''

        if not context_id:
            return Response(
                message='Error: No active context to associate questions with.',
                break_loop=False,
            )

        session = create_session(context_id, questions_raw)

        question_count = len(questions_raw)
        summary = questions_raw[0].get('question', '')
        if question_count > 1:
            summary += f' (and {question_count - 1} more)'

        AgentContext.get_notification_manager().add_notification(
            message=f'The agent is asking: {summary}',
            title='Question for You',
            detail='Click to answer in the chat panel.',
            type=NotificationType.INFO,
            priority=NotificationPriority.HIGH,
            display_time=30,
        )

        await self.set_progress('Waiting for user response...')

        try:
            await asyncio.wait_for(session.event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return Response(
                message='User did not respond within the timeout period. Please proceed with your best judgment or ask again.',
                break_loop=False,
            )

        result = session.result
        if result is None:
            return Response(
                message='Session ended without a result. Please proceed with your best judgment.',
                break_loop=False,
            )

        if result.get('cancelled', False):
            reason = result.get('reason', 'unknown')
            if reason == 'user_declined':
                return Response(
                    message='User declined to answer. They may want to continue the conversation instead. Proceed based on available information.',
                    break_loop=False,
                )
            elif reason == 'superseded':
                return Response(
                    message='This question was superseded by a newer one.',
                    break_loop=False,
                )
            else:
                return Response(
                    message=f'Question session was cancelled ({reason}). Proceed with your best judgment.',
                    break_loop=False,
                )

        answers = result.get('answers', [])
        formatted = self._format_answers(questions_raw, answers)
        return Response(message=formatted, break_loop=False)

    def _format_answers(self, questions: List[Dict], answers: List[Dict]) -> str:
        lines = ['User answered the following questions:', '']
        for ans in answers:
            idx = ans.get('question_index', 0)
            q_text = (
                questions[idx].get('question', 'Unknown')
                if idx < len(questions)
                else 'Unknown'
            )
            selected = ans.get('selected', [])
            notes = ans.get('notes', '')
            other_text = ans.get('other_text', '')

            lines.append('Q%d: %s' % (idx + 1, q_text))
            if selected:
                lines.append('  Selected: %s' % ', '.join(selected))
            if other_text:
                lines.append('  Other: %s' % other_text)
            if notes:
                lines.append('  Notes: %s' % notes)
            lines.append('')

        return '\n'.join(lines)