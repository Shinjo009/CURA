import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NutritionPlanCards } from "./NutritionPlanCards";

describe("NutritionPlanCards", () => {
  it("shows priorities, food cards and foods to limit", () => {
    render(
      <NutritionPlanCards
        plan={{
          priorities: [{ title: "More iron", why: "It carries oxygen." }],
          include: [{ name: "Spinach", why: "Iron, one bowl a day.", icon: "🥬" }, { name: "Oats" }, { name: "Curd" }],
          limit: [{ name: "Fried snacks", why: "Raise blood fats." }],
        }}
      />,
    );
    expect(screen.getByText("What your body needs")).toBeTruthy();
    expect(screen.getAllByTestId("food-include")).toHaveLength(3);
    expect(screen.getAllByTestId("food-limit")).toHaveLength(1);
    expect(screen.getByText("Foods to limit")).toBeTruthy();
  });
});
