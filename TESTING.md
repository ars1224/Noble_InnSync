# Testing Evidence

This document records the main workflows tested for the Noble InnSync final prototype. Testing was completed through manual browser checks and Flask test client smoke checks.

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

## Smoke Test Commands

Public page smoke test:

```bash
python -c "from app import create_app; app=create_app(); c=app.test_client(); print(c.get('/').status_code); print(c.get('/reservation-status').status_code)"
```

Expected output:

```text
200
200
```

Admin page smoke test:

```bash
python -c "from app import create_app; app=create_app(); c=app.test_client(); login=c.post('/auth/staff-login', data={'username':'admin','password':'admin123'}, follow_redirects=True); pages=['/admin/dashboard','/admin/inventory','/admin/equipment','/admin/activity-log','/admin/rooms','/admin/bookings','/admin/payments','/admin/reports','/admin/walk-in-booking']; print(login.status_code); [print(page, c.get(page).status_code) for page in pages]"
```

Expected result:

- Login response returns `200`.
- Each listed admin page returns `200`.
