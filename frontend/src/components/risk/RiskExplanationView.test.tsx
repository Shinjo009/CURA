import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { RiskExplanationView } from "./RiskExplanationView";
import type { RiskExplanationData } from "../../types/chat";

const data: RiskExplanationData = {
  condition_title: "What is Type 2 diabetes?",
  condition: ["Your body turns food into sugar.", "Insulin is like a key."],
  score_card: { code: "t2d", name: "Type 2 diabetes", score: 17, status: "Healthy", level: "not_raised", assessed_on: "2026-08-25", percentile: 4, lifestyle_contribution: 18, contributing_factors: ["Low activity"] },
  meaning_title: "What does this mean for you?",
  meaning: ["Your result is in the healthy band today."],
  related_tests: [{ finding: { label: "HbA1c", value: "5.2", unit: "%", status: "normal", reference_low: 4, reference_high: 5.6, numeric_value: 5.2 }, why: "Average sugar over three months." }],
  actions: [{ title: "Walk daily", detail: "30 minutes after dinner.", icon: "move" }, { title: "Sleep well", detail: "Steady bedtime.", icon: "sleep" }],
  more: [{ title: "Common signs", items: ["Feeling very thirsty"] }, { title: "What can raise this risk", items: ["Low activity"] }],
};

afterEach(cleanup);

describe("RiskExplanationView", () => {
  it("follows the four steps with the verified score and no images", () => {
    const { container } = render(<RiskExplanationView data={data} />);
    const headings = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(headings.slice(0, 3)).toEqual(["What is Type 2 diabetes?", "What does your health report say?", "What does this mean for you?"]);
    expect(headings).toContain("How can you protect your future health?");
    const card = screen.getByTestId("risk-score-card");
    expect(within(card).getByText("17")).toBeTruthy();
    expect(within(card).getByText("Healthy")).toBeTruthy();
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getAllByTestId("action-card")).toHaveLength(2);
    expect(screen.getByText("HbA1c")).toBeTruthy();
  });

  it("keeps technical details and extra reading closed until asked", () => {
    render(<RiskExplanationView data={data} />);
    expect(screen.queryByText("Percentile")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /View assessment details/ }));
    expect(screen.getByText("Percentile")).toBeTruthy();
    expect(screen.getByText(/Contributing factors in your report: Low activity/)).toBeTruthy();
    const details = document.querySelectorAll("details");
    expect(details).toHaveLength(2);
    details.forEach((d) => expect(d.open).toBe(false));
  });
});
