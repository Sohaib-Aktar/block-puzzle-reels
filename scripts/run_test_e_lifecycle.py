import os
import sys

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from campaign_manager import (
    add_or_update_item,
    advance_state,
    update_status,
    list_items,
    print_dashboard
)

print("\n--- TEST E: End-to-End Creative Approval Workflow & Gatekeeping ---")

content_id = "test-lifecycle-01"

# 1. Register new content item as IDEA and reset QC flags
add_or_update_item(
    content_id=content_id,
    project="block-puzzle-burst",
    campaign="30-day-challenge",
    topic="Test Lifecycle Item",
    platform="instagram_reel",
    status="IDEA"
)
update_status(content_id, "IDEA", technical_qc_passed=False, creative_qc_score=0)
print("1. Content item created in state: IDEA (QC flags reset)")

# 2. Advance through stages
for state in ["PLANNED", "BRIEF_APPROVED", "SCRIPT_APPROVED", "RENDERED"]:
    res = advance_state(content_id, state)
    print(f"   Advanced to: {res['new_state']}")

# 3. Test Premature Publishing Gatekeeping (Should Fail)
try:
    print("3. Attempting premature transition to READY_TO_PUBLISH before QC...")
    advance_state(content_id, "READY_TO_PUBLISH")
    print("ERROR: Premature transition succeeded when it should have been blocked!")
    sys.exit(1)
except PermissionError as e:
    print(f"   ✅ Gatekeeper blocked premature transition as expected: {e}")

# 4. Record Technical & Creative QC approvals
print("4. Recording verified Technical QC (Pass) and Creative QC (Score 84/90)...")
update_status(content_id, "QC_APPROVED", technical_qc_passed=True, creative_qc_score=84)

# 5. Advance to READY_TO_PUBLISH
res = advance_state(content_id, "READY_TO_PUBLISH")
print(f"   Advanced to: {res['new_state']}")

# 6. Test Unauthorized Publishing Gatekeeping (Should Fail without sign-off)
try:
    print("6. Attempting unauthorized publish without sign-off...")
    advance_state(content_id, "PUBLISHED")
    print("ERROR: Unauthorized publish succeeded when it should have been blocked!")
    sys.exit(1)
except PermissionError as e:
    print(f"   ✅ Gatekeeper blocked unauthorized publish as expected: {e}")

# 7. Provide Human / Editorial Sign-Off
print("7. Providing human editorial sign-off by 'Pyapiras Games Marketing Director'...")
res = advance_state(content_id, "PUBLISHED", approved_by="Pyapiras Games Marketing Director")
print(f"   ✅ Successfully published with verified sign-off! New State: {res['new_state']}")

print("\n--- Test E Passed Successfully! Lifecycle Dashboard below: ---")
print_dashboard()
