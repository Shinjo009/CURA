import type { NutritionPlanData } from "../../types/chat";
import { t } from "../../i18n";

function FoodCard({ food, tone }: { food: { name: string; why?: string; icon?: string }; tone: "include" | "limit" }) {
  return (
    <li className={`food-card food-${tone}`} data-testid={`food-${tone}`}>
      <span className="food-icon" aria-hidden="true">
        {food.icon || "🍽️"}
      </span>
      <div>
        <strong>{food.name}</strong>
        {food.why ? <p>{food.why}</p> : null}
      </div>
    </li>
  );
}

export function NutritionPlanCards({ plan }: { plan: NutritionPlanData }) {
  return (
    <div className="nutrition-plan" data-testid="nutrition-plan">
      {plan.priorities.length > 0 ? (
        <section aria-labelledby="np-needs">
          <h4 id="np-needs">{t("ui.Nutrition.needs", "What your body needs")}</h4>
          <ol className="priority-list">
            {plan.priorities.map((item, index) => (
              <li key={item.title} className="priority-card">
                <span className="priority-number" aria-hidden="true">
                  {index + 1}
                </span>
                <div>
                  <strong>{item.title}</strong>
                  {item.why ? <p>{item.why}</p> : null}
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      {plan.include.length > 0 ? (
        <section aria-labelledby="np-include">
          <h4 id="np-include">{t("ui.Nutrition.include", "Foods to include")}</h4>
          <ul className="food-grid">
            {plan.include.map((food) => (
              <FoodCard key={food.name} food={food} tone="include" />
            ))}
          </ul>
        </section>
      ) : null}
      {plan.limit.length > 0 ? (
        <section aria-labelledby="np-limit">
          <h4 id="np-limit">{t("ui.Nutrition.limit", "Foods to limit")}</h4>
          <ul className="food-grid">
            {plan.limit.map((food) => (
              <FoodCard key={food.name} food={food} tone="limit" />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
