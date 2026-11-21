import { MeetingPage } from "@/components/meeting/meeting-page"

// Live, client-loaded state: not an instant navigation by design.
export const instant = false

export default function Page() {
  return <MeetingPage />
}
