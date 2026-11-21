import type { Goal } from "@/lib/types"

const num = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 })

export function formatValue(v: number | null | undefined, unit?: string): string {
  if (v === null || v === undefined) return ""
  const n = num.format(v)
  if (unit === "%") return `${n}%`
  if (unit === "$k") return `$${n}k`
  return n
}

export function formatGoal(g: Goal, unit: string): string {
  const f = (v: number | null) => formatValue(v, unit)
  switch (g.type) {
    case "at_least": return `≥ ${f(g.value)}`
    case "at_most": return `≤ ${f(g.value)}`
    case "exactly": return `= ${f(g.value)}`
    case "between": return `${f(g.min)} to ${f(g.max)}`
  }
}

/** Issue priority: 5 is highest. */
export const PRIORITIES = [5, 4, 3, 2, 1] as const
