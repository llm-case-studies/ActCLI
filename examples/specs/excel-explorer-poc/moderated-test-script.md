# Excel Explorer POC - Moderated Test Script

**Duration:** 30-45 minutes
**Participants:** Actuarial professionals with Excel expertise
**Materials:** USGS Well_Analyses.xlsm from examples/excel-legacy/macros/

## Pre-Test Setup (5 minutes)

**Moderator Introduction:**
"Today we're testing a new tool called Excel Explorer that analyzes Excel workbooks without opening Excel or executing any macros. The goal is to help actuaries understand what's inside complex workbooks safely and quickly."

**Safety Explanation:**
"Important: This tool never executes macros or runs calculations. It reads the file structure like inspecting a ZIP file. You'll see a 'No Execution' badge throughout the interface."

**File Introduction:**
"We'll use a real USGS hydrology workbook with macros and formulas. This represents the complexity you might see in actuarial models."

## Task Sequence

### Task 1: VBA Discovery (8 minutes)
**Instruction:** "Find the Auto_Open macro and show me its code."

**Expected Path:**
1. Navigate to VBA section in tree
2. Expand modules to find `ThisWorkbook`
3. Locate `Workbook_Open` procedure (auto-exec)
4. View code in right panel

**Success Criteria:**
- ✅ Located auto-exec procedure < 60 seconds
- ✅ Can read VBA code clearly
- ✅ Notices "autoexec: true" indicator

**Observation Notes:**
- Time to find: _____ seconds
- Confusion points: _____________
- Confidence in code accuracy (1-7): _____

### Task 2: Named Range Analysis (8 minutes)
**Instruction:** "Which named ranges are used for well data analysis? Show me their scope and where they're referenced."

**Expected Path:**
1. Navigate to Named Ranges section
2. Find `WellData_Range` and related ranges
3. View scope (workbook vs sheet level)
4. Check "used_by_count" details

**Success Criteria:**
- ✅ Identified key data ranges < 60 seconds
- ✅ Distinguished workbook vs sheet scope
- ✅ Understood usage frequency

**Observation Notes:**
- Time to complete: _____ seconds
- Scope understanding: Clear / Confused
- Trust in "used by" counts (1-7): _____

### Task 3: Formula Complexity (10 minutes)
**Instruction:** "Show me the most common formula patterns and identify any 'volatile' functions that could slow down calculations."

**Expected Path:**
1. Navigate to Formulas section
2. Review top formula families
3. Check volatiles tab for OFFSET/INDIRECT
4. Examine complexity metrics

**Success Criteria:**
- ✅ Found formula families < 60 seconds
- ✅ Identified volatile functions
- ✅ Understood performance implications

**Observation Notes:**
- Time to insights: _____ seconds
- Pattern recognition: Clear / Unclear
- Volatile function understanding (1-7): _____

### Task 4: External Dependencies (5 minutes)
**Instruction:** "Check if this workbook connects to external databases or other files."

**Expected Path:**
1. Navigate to Connections section
2. Review external references in Formulas detail
3. Note absence of external connections

**Success Criteria:**
- ✅ Confirmed no external connections < 30 seconds
- ✅ Understood security implications

**Observation Notes:**
- Time to confirm: _____ seconds
- Security confidence (1-7): _____

### Task 5: Hidden Content (5 minutes)
**Instruction:** "Are there any hidden or very hidden sheets? What might they contain?"

**Expected Path:**
1. Navigate to Sheets section
2. Identify "Validation" sheet marked as "hidden"
3. Review its stats (formulas, cells)

**Success Criteria:**
- ✅ Found hidden sheet < 30 seconds
- ✅ Assessed content without opening

**Observation Notes:**
- Time to find: _____ seconds
- Understanding of hidden content: _____________

## Post-Task Interview (8 minutes)

### Trust & Confidence
1. **"Rate your confidence (1-7) that this tool sees what Excel sees."**
   - Score: _____
   - Reasoning: _____________

2. **"What made you trust (or doubt) the information shown?"**
   - Trust factors: _____________
   - Doubt factors: _____________

3. **"How important is the 'No Execution' safety guarantee?"**
   - Very Important / Somewhat / Not Important
   - Reasoning: _____________

### Usability & Clarity
4. **"Which sections were easiest/hardest to navigate?"**
   - Easiest: _____________
   - Hardest: _____________

5. **"What felt missing before you'd trust this for parity checks?"**
   - Missing features: _____________

6. **"Would you use this before opening an unknown Excel file?"**
   - Yes / No / Maybe
   - Reasoning: _____________

### Business Value
7. **"How would this fit into your current Excel analysis workflow?"**
   - Current process: _____________
   - Potential improvements: _____________

8. **"What's the biggest risk this tool would help you avoid?"**
   - Primary risk: _____________
   - Secondary risks: _____________

## Scoring Rubric

### Speed (Target: <60s per task)
- **Excellent:** All tasks completed under target
- **Good:** 1-2 tasks over target
- **Needs Work:** 3+ tasks over target

### Trust (Target: 5+ on confidence scale)
- **High Trust:** Score 6-7, clear reasoning
- **Moderate Trust:** Score 4-5, some concerns
- **Low Trust:** Score 1-3, significant doubts

### Safety Understanding
- **Clear:** Understands "No Execution" guarantee
- **Partial:** Generally understands, some confusion
- **Unclear:** Doesn't grasp safety implications

### Business Readiness
- **Ready:** Would use in current workflow
- **Close:** Minor concerns, mostly ready
- **Not Ready:** Significant barriers to adoption

## Success Metrics (POC Validation)

**Minimum Viable POC:**
- ✅ 80% of participants complete all tasks
- ✅ Average confidence score ≥ 5.0
- ✅ 70% would use in current workflow
- ✅ Zero critical safety misunderstandings

**Strong POC (Ready for Integration):**
- ✅ 90% of participants complete all tasks under time targets
- ✅ Average confidence score ≥ 6.0
- ✅ 85% would use in current workflow
- ✅ Clear articulation of business value

## Notes Section

**Technical Issues Observed:**
_____________

**UI/UX Improvements Needed:**
_____________

**Feature Requests:**
_____________

**Unexpected User Behaviors:**
_____________

---

**Next Steps Based on Results:**
- **Strong Performance:** Proceed with ActCLI integration
- **Good Performance:** Address top 2-3 issues, re-test
- **Poor Performance:** Redesign core UX, fundamental changes needed