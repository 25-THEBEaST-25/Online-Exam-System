# Online Exam System - Fix Errors TODO

## Plan Breakdown (Approved)
1. ✅ **Created TODO.md** - Track progress
2. **Edit app.py** 
   - [x] Update DB_CONFIG password to user-provided
   - [x] Add missing route: GET /admin/students → students.html
   - [x] Add missing route: GET /admin/exams → view_exams.html
   - [x] Add missing route: GET /admin/results (?student=) → all_results.html with filter
   - [x] Add error handlers (404/500, DB connection)
   - [x] Update app.run(host='0.0.0.0')
3. **Test app** ✅
   - [x] Run `python app.py`
   - [x] Test login/register/admin/student/exam flows
   - [x] Verify no crashes, all nav links work
4. **Cleanup** (optional) ✅
   - [x] Remove unused templates
5. **attempt_completion** ✅
