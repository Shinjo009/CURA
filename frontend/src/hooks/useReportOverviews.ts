import { useQuery } from "@tanstack/react-query";
import { getBodySystems, getRiskOverview } from "../lib/api";
import { queryKeys } from "../lib/queryClient";

/** Structured overview of a blood report. No model call, so it is quick to open. */
export function useBodySystems(reportId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.bodySystems(reportId),
    queryFn: () => getBodySystems(reportId),
    enabled,
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useRiskOverview(reportId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.riskOverview(reportId),
    queryFn: () => getRiskOverview(reportId),
    enabled,
    staleTime: 5 * 60_000,
    retry: false,
  });
}
