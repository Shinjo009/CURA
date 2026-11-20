const NAMES: Record<string, string> = {
  heart_circulation: "Heart & Circulation",
  liver_health: "Liver Health",
  kidney_urinary: "Kidney & Urinary",
  blood_iron: "Blood & Iron",
  blood_sugar_metabolism: "Blood Sugar & Metabolism",
  vitamins_nutrition: "Vitamins & Nutrition",
  thyroid_health: "Thyroid Health",
  hormonal_health: "Hormonal Health",
  bone_mineral: "Bone & Mineral Health",
  immunity_inflammation: "Immunity & Inflammation",
  cancer_related: "Cancer-Related Markers",
  sleep_recovery: "Sleep & Recovery",
  other_unmapped: "Other results",
  allergy: "Allergy",
};

/** Display name for a cross-reference id. The summary's own name is always preferred where present. */
export function systemName(id: string): string {
  return NAMES[id] || id.replace(/_/g, " ");
}
