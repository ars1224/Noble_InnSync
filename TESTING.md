# Testing Evidence

This document records the automated and manual checks for the Noble InnSync final prototype. Automated tests run against a temporary in-memory SQLite database, so they do not read from or change `instance/noble_innsync.db`.

## Automated Test Suite

Run all automated tests from the project root:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

The command must finish with `OK`. The suite currently checks:

- Public homepage, reservation lookup, availability search, and legacy login routes.
- Search values remaining visible on the available rooms page.
- Missing, malformed, same-day, and reversed stay dates.
- Correct multi-night pricing and the 15% tax/fees calculation.
- Single Room capacity enforcement.
- Maintenance rooms being excluded from available room options.
- Temporary room holds being released after failed payment.
- Successful payment creating one booking and one accounting record.
- Duplicate payment submission being rejected without creating another booking.
- Lapsed active bookings being cancelled and paid card records being refunded.
- Maintenance reports requiring details, creating equipment issues, and supporting repeat reports.
- Inventory item creation, editing, restocking, category filter markup, and manager alerts.
- Equipment issue reporting, maintenance requests, and manager resolution.
- Booking approval, check-in, check-out, editing, payment updates, and cancellation.
- Walk-in bookings creating accounting records and marking rooms occupied.
- Admin room creation, editing, and deletion.
- Confirmation actions returning home and print rules excluding navigation and the footer.
- Successful login, incorrect passwords, inactive accounts, and logout.
- Unauthenticated users being redirected to staff login.
- Staff and manager role restrictions.
- Authenticated admin pages reaching the requested page instead of a redirected login page.
- Key pages not referencing missing local CSS, JavaScript, or image files.

The suite currently contains 22 isolated tests.

The automated users and passwords exist only inside the temporary test database. They are not application credentials.

## Guest Workflows

- Homepage loads and navigation links work.
- Room availability search accepts check-in date, check-out date, adults, and children.
- Available rooms page displays matching room types and keeps search values visible.
- Edit search works directly on the available rooms page without returning to the homepage.
- Room details page displays room photos, amenities, capacity, room price, and booking actions.
- Smart room allocation suggests suitable rooms based on adult and child guest count.
- Single Room cannot be booked when the guest count exceeds room capacity.
- Booking review displays guest details, stay dates, room details, and total price including 15% tax/fees.
- Payment success confirms the booking and creates reservation details.
- Failed and pending payment paths release temporary room holds back to availability.
- Reservation status lookup displays the booking reference, room details, guest count, payment status, and total price.
- Print Reservation opens the browser print dialog so guests can print or save the reservation as PDF.

## Staff Workflows

- Staff login page loads at `/auth/staff-login`.
- Staff dashboard loads after authentication.
- Walk-in booking workflow loads and supports room selection, guest details, and payment details.
- Booking management page loads and allows staff to review booking records.
- Room management page loads and supports room status updates.
- Inventory page loads and supports adding or managing supply records.
- Equipment page loads and supports reporting or reviewing equipment issues.
- Activity log page loads and shows operational follow-up records.

## Admin Workflows

- Admin account can log in successfully.
- Admin dashboard loads with operational metrics, attention queue, room inventory, and recent bookings.
- Booking detail, edit, payment, and status workflows are accessible from the admin area.
- Room create, edit, delete, and status update workflows are available to admin users.
- Payment status management page loads successfully.
- Inventory monitoring and equipment tracking pages load successfully.
- Admin controls remain inside their cards on medium screen sizes.

## Manager Workflows

- Manager account can log in successfully.
- Manager dashboard loads with role-appropriate navigation.
- Reports page loads with revenue, payment, booking, and room utilization sections.
- Inventory, equipment, and activity log pages are available for review.
- Manager-only reporting links and dashboard actions display correctly.

## Responsive Checks

The following screen categories were checked manually:

- Desktop: wide laptop/monitor layout.
- Medium screen: dashboard layout around tablet/small laptop width.
- Tablet: stacked cards, wrapped action buttons, and scrollable tables.
- Mobile: single-column guest booking and room browsing flows.

Responsive behavior checked:

- Buttons remain inside their cards.
- Dashboard forms wrap instead of overflowing.
- Tables use horizontal scrolling where needed.
- Guest booking text and buttons remain readable.
- Navigation remains usable on smaller screens.

Record the browser name, viewport width, date, result, and any screenshot for each manual responsive run. Suggested exact widths are `1440px`, `1024px`, `768px`, and `390px`.

## Quick Smoke Checks

The full automated suite above is the preferred check. For a quick public-page check only, run:

```bash
python -c "from app import create_app; app=create_app(); c=app.test_client(); print(c.get('/').status_code); print(c.get('/reservation-status').status_code)"
```

Expected output:

```text
200
200
```

Do not use `follow_redirects=True` plus status codes alone to verify protected pages. A failed login can redirect back to the login page and still finish with `200`. The automated suite verifies both authentication and the final requested path.

## Manual Evidence Record

For each manual session, record:

- Date and tester.
- Browser and viewport size.
- Test data used, without real payment or personal information.
- Expected result and actual result.
- Pass or fail.
- Screenshot or defect reference when relevant.

## Remaining Security Checks

Before production deployment, add CSRF protection and convert state-changing admin links such as approve, cancel, delete, and status changes to POST requests. Then add automated tests confirming GET requests cannot change application data.
