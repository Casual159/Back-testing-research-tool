---
date: YYYY-MM-DD
session_id: cs_xxxxxx
human: Jakub
ai_model: claude-sonnet-4.5
topic: Brief Topic Description
status: ✅ Completed | 🚧 In Progress | ❌ Blocked
tags: #session #component/[name] #feature/[name]
---

# Session: [Topic Title]

**Session Date:** YYYY-MM-DD  
**Duration:** ~X hours  
**Status:** ✅ Completed / 🚧 In Progress / ❌ Blocked

---

## 🎯 Goal

[Clear statement of what this session aimed to accomplish]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

---

## 🔨 What We Did

### Summary
[1-2 sentence overview of what was accomplished]

### Detailed Steps
1. **[Step 1 Title]**
   - Action taken
   - Result
   - Files affected: `path/to/file.py:line-range`

2. **[Step 2 Title]**
   - Action taken
   - Result
   - Files affected: `path/to/file.py:line-range`

3. **[Continue...]**

---

## 📊 Files Changed

### Created Files
- `path/to/new/file.py` (XX lines)
  - Purpose: What this file does
  - Key functions: `function1()`, `function2()`

### Modified Files
- `path/to/existing/file.py` (+XX/-YY lines)
  - Changes: What was changed and why
  - Lines: XX-YY

### Deleted Files
- `path/to/old/file.py`
  - Reason: Why it was deleted

---

## 🧠 Key Decisions

### Decision 1: [Title]
**Context:** Why we needed to decide  
**Options Considered:**
1. Option A - Pros/Cons
2. Option B - Pros/Cons

**Decision:** Option X  
**Rationale:** Why we chose this  
**Trade-offs:** What we gave up

### Decision 2: [Continue...]

---

## 💡 Technical Insights

### What Worked Well
- ✅ Insight 1
- ✅ Insight 2

### What Was Challenging
- ⚠️ Challenge 1 - How we overcame it
- ⚠️ Challenge 2 - How we overcame it

### Patterns Used
- Pattern 1: Description
- Pattern 2: Description

---

## 🚨 Issues Encountered

### Issue 1: [Title]
**Problem:** Description of the problem  
**Root Cause:** Why it happened  
**Solution:** How we fixed it  
**Prevention:** How to avoid in future

### Issue 2: [Continue...]

---

## 🧪 Testing Done

### Manual Tests
```bash
# Commands run
python api/main.py
curl http://localhost:8000/api/endpoint
```

**Results:**
- ✅ Test 1 passed
- ✅ Test 2 passed
- ❌ Test 3 failed (if applicable, explain)

### Edge Cases Tested
- [ ] Edge case 1
- [ ] Edge case 2

---

## 📝 Documentation Updated

### Files Updated
- [ ] [[02-Components/_AI_CONTEXT]] - Added new component
- [ ] [[02-Components/Component Name]] - Created detailed doc
- [ ] [[05-Reference/_GENERATED/README]] - Regenerated docs
- [ ] This session note

### Auto-Generated Docs
```bash
# Scripts run
python scripts/generate_api_docs.py
python scripts/generate_db_schema.py
```

---

## 📋 For Next Session

### Immediate Next Steps
- [ ] Task 1 - Description
- [ ] Task 2 - Description
- [ ] Task 3 - Description

### Future Improvements
- Idea 1
- Idea 2

### Open Questions
- Question 1?
- Question 2?

---

## 🔗 Related Documentation

**Updated:**
- [[Component or Feature Doc]]
- [[Related Context File]]

**Related Sessions:**
- [[99-Meta/AI_Session_Notes/YYYY-MM-DD_related_topic]]

**External References:**
- [Link to external doc](https://example.com)

---

## 📈 Metrics (if applicable)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| API response time | Xms | Yms | +/-Z% |
| Lines of code | X | Y | +/-Z |
| Test coverage | X% | Y% | +/-Z% |

---

## 🎓 Lessons Learned

### For AI
- Lesson 1: What AI learned about the codebase
- Lesson 2: What pattern to follow in future

### For Humans
- Lesson 1: Important insight for developers
- Lesson 2: Gotcha to remember

---

## 🤖 AI Summary for Next Session

[Write a concise 2-3 sentence summary that another AI session can read to understand what was accomplished. Include key context that would be helpful for continuation.]

**Key Context:**
- Component X was implemented in `file.py:lines`
- Decision Y was made for reason Z
- Next step is to implement feature W

---

## 📎 Code Snippets (Optional)

### Important Code Added

```python
# file.py:XX-YY
def important_function(param: Type) -> ReturnType:
    """
    Brief description of what this does
    """
    # Implementation
    pass
```

### Configuration Changes

```python
# config.py
NEW_SETTING = "value"  # Why this was added
```

---

**Session Completed:** YYYY-MM-DD HH:MM  
**Next Session:** [[99-Meta/AI_Session_Notes/YYYY-MM-DD_next_topic]]

---

_This session note is part of the project's living documentation. Update [[Project Root]] and relevant component docs if major changes were made._
