"""
Ticket CRUD endpoints, called by n8n.

/tickets/create        -> called right at intake (Day 1-2 reliability fix:
                           ticket exists in "Processing" state before any
                           AI work happens, so nothing is lost on failure)
/tickets/{id}/update    -> called after AI processing to set final
                           status, priority, confidence, assigned_team etc.

Built: Day 7-8 (structured ticket creation)
"""
