# Milestone 3 live demonstration and feedback

Smart Campus Parking - Samarth Thakor and Nirmal Naik  
Class demonstration: October 22, 2026. Submission: October 23, 2026.

## Five-minute demonstration

1. **Problem (30 seconds):** Students need permitted parking near their next class.
   Our app combines their weekly schedule with manually reported lot availability.
2. **Student flow (90 seconds):** Create an account, save a Student permit, and add a
   class at Library Building tomorrow at 10:00. Show the saved schedule and Lot B.
   Explain the accepted permits, five-minute walk and availability timestamp.
3. **Persistence (45 seconds):** Stop and restart Flask. Sign in again and show that
   the schedule remains. Explain that migrations run automatically before requests.
4. **Administrator flow (60 seconds):** Use a separate browser session as Jordan.
   Close Lot B, save, and refresh the student page. Show Lot A as the replacement.
5. **Quality (30 seconds):** Show the passing PR workflow, test report and coverage.
   Enter an invalid end time and show the validation error.
6. **Questions (45 seconds):** Ask whether the availability wording is clear, whether
   class entry is easy, and which feature should come next. Reopen Lot B afterward.

The data is fictional. The demonstration does not claim live university integration,
space reservations, a deployed AWS service, or guaranteed future availability.

## Feedback received

Status on October 20, 2026: the scheduled classroom demonstration has not occurred.
Actual peer and instructor feedback is pending. Complete this record after class,
then update Section 4 of the PDF before submitting.

| Source and date | Actual feedback | Decision / next action | Owner | Target |
|---|---|---|---|---|
| Instructor, Oct 22 | Pending classroom demonstration | Record feedback and priority | Team | Before Oct 23 submission |
| Peers, Oct 22 | Pending classroom demonstration | Record feedback and priority | Team | Before Oct 23 submission |

## Proposed priorities before feedback

These are team planning proposals, not feedback already received.

1. Fix any failure discovered in the live workflow; retest before adding features.
2. Improve navigation, wording and form usability based on actual classroom feedback
   (Samarth; first development cycle after the demonstration).
3. Validate MySQL migrations and an AWS deployment path (Nirmal; subsequent cycle).
4. Add an optional map only if time allows after core reliability and usability work
   (both members). Retain stored walking estimates until a route service is verified.

After feedback, classify each item as required for reliability, useful for usability,
or optional. Assign an owner, define an acceptance check and record any deferred work.
