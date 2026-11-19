from app.auth.models import AuthenticatedPrincipal
from app.contracts.questionnaire import QuestionnaireAnswer, QuestionnaireInstance
from app.contracts.query import QueryPlan
from app.pipeline.questionnaire_topics import keys_for_plan
from integrations.mock.loader import load_json


class MockQuestionnaireProvider:
    def __init__(self) -> None:
        self._rows = load_json("questionnaires.json")

    def load_for_cache(self, principal: AuthenticatedPrincipal, scope: str) -> list[QuestionnaireInstance]:
        """Every instance with every answer, not shaped by any question, so the cache can be shared."""
        subject = (principal.subject_id or "").strip()
        instances: list[QuestionnaireInstance] = []
        for row in self._rows:
            if row.get("subject_id") != subject:
                continue
            for raw in row.get("instances") or []:
                answers = [
                    QuestionnaireAnswer(
                        response_id=str(item["response_id"]),
                        assessment_instance_id=str(raw["assessment_instance_id"]),
                        question_id=str(item["question_id"]),
                        question_key=item["question_key"],
                        question=item["question"],
                        value=item.get("value"),
                        unit=item.get("unit"),
                        response_type=item.get("response_type") or "text",
                        recorded_at=raw.get("recorded_at"),
                        subject_id=subject,
                    )
                    for item in raw.get("answers") or []
                ]
                instances.append(
                    QuestionnaireInstance(
                        assessment_instance_id=str(raw["assessment_instance_id"]),
                        subject_id=subject,
                        package_code=raw.get("package_code"),
                        status=raw.get("status"),
                        recorded_at=raw.get("recorded_at"),
                        answers=answers,
                    )
                )
        instances.sort(key=lambda item: (str(item.recorded_at or ""), item.assessment_instance_id))
        return instances

    def query(self, principal: AuthenticatedPrincipal, plan: QueryPlan) -> list[QuestionnaireInstance]:
        return self.apply_plan(self.load_for_cache(principal, "history"), plan)

    def apply_plan(self, instances: list[QuestionnaireInstance], plan: QueryPlan) -> list[QuestionnaireInstance]:
        wanted_set = set(keys_for_plan(plan.topic, plan.requested_metrics, plan.raw_message or ""))
        keep_history = bool(plan.history or plan.compare or plan.time_operation in {"trend", "previous", "compare"})
        shaped = [
            instance.model_copy(update={"answers": [a for a in instance.answers if a.question_key in wanted_set]})
            for instance in instances
        ]
        return shaped if keep_history else shaped[-1:]
