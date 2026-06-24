import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models.activity_log import ActivityLog
from app.models.accounting import Accounting
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.equipment import EquipmentIssue
from app.models.inventory import InventoryItem
from app.models.room import Room
from app.models.user import User
from app.utils.pricing import calculate_nights, calculate_stay_total


class NobleInnSyncTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

        self._add_user("admin", "admin", "admin-pass")
        self._add_user("staff", "staff", "staff-pass")
        self._add_user("manager", "manager", "manager-pass")
        self._add_user("inactive", "staff", "inactive-pass", status="Inactive")

        db.session.add_all([
            Room(
                room_number="101",
                room_type="Single Room",
                description="Test single room",
                price=149,
                status="Available",
            ),
            Room(
                room_number="201",
                room_type="Double Room",
                description="Test double room",
                price=229,
                status="Available",
            ),
            Room(
                room_number="301",
                room_type="Family Room",
                description="Test family room",
                price=329,
                status="Available",
            ),
            Room(
                room_number="205",
                room_type="Double Room",
                description="Room under maintenance",
                price=229,
                status="Maintenance",
            ),
        ])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _add_user(self, username, role, password, status="Active"):
        user = User(
            username=username,
            role=role,
            full_name=f"{role.title()} Test User",
            status=status,
        )
        user.set_password(password)
        db.session.add(user)

    def _login(self, username, password):
        return self.client.post(
            "/auth/staff-login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def _single_room(self):
        return Room.query.filter_by(room_number="101").one()

    def _guest_form(self):
        return {
            "first_name": "Jamie",
            "last_name": "Tester",
            "email": "jamie@example.com",
            "phone": "0211234567",
            "check_in": "2030-01-10",
            "check_out": "2030-01-12",
            "adults": "1",
            "children": "0",
        }

    def _create_booking(self, reference="NIS-ADMIN", room=None, status="Pending"):
        room = room or self._single_room()
        check_in = (date.today() + timedelta(days=10)).isoformat()
        check_out = (date.today() + timedelta(days=12)).isoformat()
        booking = Booking(
            reference_number=reference,
            guest_name="Admin Flow Guest",
            email="admin-flow@example.com",
            phone="0219999999",
            check_in=check_in,
            check_out=check_out,
            adults=1,
            children=0,
            total_price=342.7,
            status=status,
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add(BookingRoom(
            booking_id=booking.id,
            room_number=room.room_number,
            room_type=room.room_type,
            price=room.price,
            adult_capacity=1,
            child_capacity=0,
        ))
        db.session.add(Accounting(
            transaction_no=f"TXN-{reference}",
            booking_id=booking.id,
            check_in=check_in,
            check_out=check_out,
            total_price=booking.total_price,
            payment_status="Unpaid",
            payment_method="Pay on Arrival",
        ))
        room.status = "Reserved"
        db.session.commit()
        return booking

    def test_public_pages_and_legacy_login_route_load(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/reservation-status").status_code, 200)

        response = self.client.get("/login", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/auth/staff-login"))

    def test_availability_search_preserves_values(self):
        response = self.client.get(
            "/available-rooms",
            query_string={
                "check_in": "2030-01-10",
                "check_out": "2030-01-12",
                "adults": "2",
                "children": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2030-01-10", response.data)
        self.assertIn(b"2030-01-12", response.data)

    def test_pricing_rejects_missing_invalid_and_reversed_dates(self):
        invalid_dates = [
            ("", "2030-01-12"),
            ("not-a-date", "2030-01-12"),
            ("2030-01-12", "2030-01-12"),
            ("2030-01-13", "2030-01-12"),
        ]

        for check_in, check_out in invalid_dates:
            with self.subTest(check_in=check_in, check_out=check_out):
                with self.assertRaises(ValueError):
                    calculate_nights(check_in, check_out)

        self.assertEqual(calculate_stay_total(149, "2030-01-10", "2030-01-12"), (2, 298.0))

    def test_single_room_rejects_guests_over_capacity(self):
        room = self._single_room()
        form = self._guest_form()
        form["adults"] = "2"

        response = self.client.post(f"/rooms/{room.id}/review", data=form)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"fits up to 1 adult", response.data)

    def test_failed_payment_releases_temporary_hold(self):
        room = self._single_room()
        form = self._guest_form()

        hold_response = self.client.post(f"/rooms/{room.id}/hold", data=form)
        self.assertEqual(hold_response.status_code, 200)
        self.assertEqual(db.session.get(Room, room.id).status, "On Hold")

        failed_response = self.client.post(f"/rooms/{room.id}/payment/failed", data=form)
        self.assertEqual(failed_response.status_code, 200)
        self.assertEqual(db.session.get(Room, room.id).status, "Available")

    def test_successful_payment_creates_one_booking_and_accounting_record(self):
        room = self._single_room()
        form = self._guest_form()
        self.client.post(f"/rooms/{room.id}/hold", data=form)

        response = self.client.post(f"/rooms/{room.id}/payment/success", data=form)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.get(Room, room.id).status, "Booked")
        self.assertEqual(Booking.query.count(), 1)
        self.assertEqual(Accounting.query.count(), 1)
        self.assertEqual(Booking.query.one().total_price, 342.7)
        self.assertEqual(Accounting.query.one().payment_status, "Paid")
        self.assertIn(b"Go Back Home", response.data)
        self.assertNotIn(b"View Status", response.data)

        duplicate = self.client.post(f"/rooms/{room.id}/payment/success", data=form)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(Booking.query.count(), 1)

    def test_maintenance_room_is_excluded_from_room_suggestions(self):
        response = self.client.get(
            "/available-room-options",
            query_string={"check_in": "2030-01-10", "check_out": "2030-01-12"},
        )

        self.assertEqual(response.status_code, 200)
        room_numbers = {room["room_number"] for room in response.get_json()["rooms"]}
        self.assertNotIn("205", room_numbers)

    def test_lapsed_booking_is_cancelled_and_paid_card_is_refunded(self):
        room = self._single_room()
        room.status = "Reserved"
        booking = Booking(
            reference_number="NIS-LAPSED",
            guest_name="Past Guest",
            email="past@example.com",
            phone="0210000000",
            check_in=(date.today() - timedelta(days=4)).isoformat(),
            check_out=(date.today() - timedelta(days=1)).isoformat(),
            adults=1,
            children=0,
            total_price=149,
            status="Confirmed",
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add(BookingRoom(
            booking_id=booking.id,
            room_number=room.room_number,
            room_type=room.room_type,
            price=room.price,
            adult_capacity=1,
            child_capacity=0,
        ))
        db.session.add(Accounting(
            transaction_no="TXN-LAPSED",
            booking_id=booking.id,
            check_in=booking.check_in,
            check_out=booking.check_out,
            total_price=booking.total_price,
            payment_status="Paid",
            payment_method="Card",
        ))
        db.session.commit()

        self.client.get("/")

        self.assertEqual(db.session.get(Booking, booking.id).status, "Cancelled")
        self.assertEqual(Accounting.query.one().payment_status, "Refunded")
        self.assertEqual(db.session.get(Room, room.id).status, "Available")

    def test_room_maintenance_requires_details_and_logs_them(self):
        self._login("staff", "staff-pass")
        room = self._single_room()

        missing_details = self.client.post(
            f"/admin/rooms/{room.id}/update-status",
            data={"status": "Maintenance"},
        )
        self.assertEqual(missing_details.status_code, 400)
        self.assertEqual(db.session.get(Room, room.id).status, "Available")

        response = self.client.post(
            f"/admin/rooms/{room.id}/update-status",
            data={
                "status": "Maintenance",
                "equipment_name": "Bathroom sink",
                "issue_status": "Broken",
                "priority": "High",
                "notes": "Water is leaking beneath the bathroom sink.",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(db.session.get(Room, room.id).status, "Maintenance")
        issue = EquipmentIssue.query.one()
        self.assertEqual(issue.equipment_name, "Bathroom sink")
        self.assertEqual(issue.status, "Broken")
        self.assertEqual(issue.priority, "High")
        self.assertEqual(issue.maintenance_status, "Requested")
        self.assertIn("Water is leaking", ActivityLog.query.one().message)

        repeated_without_details = self.client.post(
            f"/admin/rooms/{room.id}/update-status",
            data={"status": "Maintenance"},
        )
        self.assertEqual(repeated_without_details.status_code, 400)

        repeated_report = self.client.post(
            f"/admin/rooms/{room.id}/update-status",
            data={
                "status": "Maintenance",
                "equipment_name": "Air conditioner",
                "issue_status": "Check Needed",
                "priority": "Medium",
                "notes": "Unit is making a loud rattling noise.",
            },
        )
        self.assertEqual(repeated_report.status_code, 302)
        self.assertEqual(EquipmentIssue.query.count(), 2)

    def test_room_maintenance_modal_and_inventory_filters_are_rendered(self):
        db.session.add_all([
            InventoryItem(item_name="Towels", category="Housekeeping", current_stock=4),
            InventoryItem(item_name="Coffee pods", category="Food and Beverage", current_stock=20),
        ])
        db.session.commit()
        self._login("admin", "admin-pass")

        rooms_page = self.client.get("/admin/rooms").get_data(as_text=True)
        inventory_page = self.client.get("/admin/inventory").get_data(as_text=True)

        self.assertIn("data-maintenance-modal", rooms_page)
        self.assertIn("equipment_name", rooms_page)
        self.assertIn("issue_status", rooms_page)
        self.assertIn("priority", rooms_page)
        self.assertIn("Short issue notes", rooms_page)
        self.assertIn('data-inventory-filter="Housekeeping"', inventory_page)
        self.assertIn('data-inventory-category="Food and Beverage"', inventory_page)

    def test_inventory_add_edit_restock_and_alert_workflow(self):
        self._login("staff", "staff-pass")

        added = self.client.post("/admin/inventory/add", data={
            "item_name": "Laundry Bags",
            "category": "Housekeeping",
            "current_stock": "3",
            "reorder_level": "8",
            "unit": "packs",
        })
        self.assertEqual(added.status_code, 302)
        item = InventoryItem.query.filter_by(item_name="Laundry Bags").one()

        updated = self.client.post(f"/admin/inventory/{item.id}/update", data={
            "item_name": "Laundry Bags",
            "category": "Cleaning Supplies",
            "current_stock": "5",
            "reorder_level": "10",
            "unit": "bundles",
        })
        self.assertEqual(updated.status_code, 302)
        self.assertEqual(item.category, "Cleaning Supplies")
        self.assertEqual(item.current_stock, 5)

        restocked = self.client.post(
            f"/admin/inventory/{item.id}/add-stock",
            data={"quantity": "7"},
        )
        self.assertEqual(restocked.status_code, 302)
        self.assertEqual(item.current_stock, 12)

        alerted = self.client.post(f"/admin/inventory/{item.id}/send-alert")
        self.assertEqual(alerted.status_code, 302)
        self.assertIn("Low-stock alert", ActivityLog.query.order_by(ActivityLog.id.desc()).first().message)

    def test_equipment_report_request_and_resolution_workflow(self):
        room = self._single_room()
        self._login("staff", "staff-pass")

        reported = self.client.post("/admin/equipment/report", data={
            "room_id": str(room.id),
            "equipment_name": "Door lock",
            "status": "Broken",
            "priority": "High",
            "notes": "Key card does not unlock the door.",
        })
        self.assertEqual(reported.status_code, 302)
        issue = EquipmentIssue.query.filter_by(equipment_name="Door lock").one()

        requested = self.client.post(f"/admin/equipment/{issue.id}/request-maintenance")
        self.assertEqual(requested.status_code, 302)
        self.assertEqual(issue.maintenance_status, "Requested")
        self.assertEqual(room.status, "Maintenance")

        self.client.post("/auth/logout")
        self._login("manager", "manager-pass")
        resolved = self.client.post(f"/admin/equipment/{issue.id}/resolve")
        self.assertEqual(resolved.status_code, 302)
        self.assertEqual(issue.status, "Working")
        self.assertEqual(issue.maintenance_status, "Resolved")
        self.assertEqual(room.status, "Available")

    def test_booking_status_edit_and_payment_management_workflow(self):
        booking = self._create_booking()
        room = self._single_room()
        payment = booking.accounting[0]
        self._login("staff", "staff-pass")

        self.client.get(f"/admin/bookings/{booking.id}/approve")
        self.assertEqual(booking.status, "Confirmed")
        self.assertEqual(room.status, "Reserved")

        self.client.get(f"/admin/bookings/{booking.id}/update-status/checked-in")
        self.assertEqual(booking.status, "Checked In")
        self.assertEqual(room.status, "Occupied")

        self.client.get(f"/admin/bookings/{booking.id}/update-status/checked-out")
        self.assertEqual(booking.status, "Checked Out")
        self.assertEqual(room.status, "Available")

        new_check_in = (date.today() + timedelta(days=20)).isoformat()
        new_check_out = (date.today() + timedelta(days=23)).isoformat()
        edited = self.client.post(f"/admin/bookings/{booking.id}/edit", data={
            "guest_name": "Edited Guest",
            "email": "edited@example.com",
            "phone": "0211111111",
            "check_in": new_check_in,
            "check_out": new_check_out,
            "adults": "1",
            "children": "0",
            "status": "Confirmed",
        })
        self.assertEqual(edited.status_code, 302)
        self.assertEqual(booking.guest_name, "Edited Guest")
        self.assertEqual(booking.total_price, 514.05)
        self.assertEqual(room.status, "Reserved")
        self.assertEqual(payment.check_out, new_check_out)

        payment_update = self.client.post(
            f"/admin/bookings/{booking.id}/payment",
            data={"payment_status": "Paid", "payment_method": "Card"},
        )
        self.assertEqual(payment_update.status_code, 302)
        self.assertEqual(payment.payment_status, "Paid")
        self.assertEqual(payment.payment_method, "Card")

        self.client.get(f"/admin/bookings/{booking.id}/cancel")
        self.assertEqual(booking.status, "Cancelled")
        self.assertEqual(room.status, "Available")

    def test_walkin_booking_creates_payment_and_occupies_room(self):
        room = self._single_room()
        self._login("staff", "staff-pass")
        check_in = (date.today() + timedelta(days=1)).isoformat()
        check_out = (date.today() + timedelta(days=3)).isoformat()

        response = self.client.post("/admin/walk-in-booking", data={
            "room_ids": str(room.id),
            "guest_name": "Walk-in Guest",
            "email": "walkin@example.com",
            "phone": "0212222222",
            "check_in": check_in,
            "check_out": check_out,
            "adults": "1",
            "children": "0",
            "payment_status": "Paid",
            "payment_method": "Cash",
        })

        self.assertEqual(response.status_code, 302)
        walkin = Booking.query.filter(Booking.reference_number.like("WALK-%")).one()
        self.assertEqual(walkin.status, "Checked In")
        self.assertEqual(walkin.accounting[0].payment_method, "Cash")
        self.assertEqual(room.status, "Occupied")

    def test_admin_room_create_edit_and_delete_workflow(self):
        self._login("admin", "admin-pass")
        created = self.client.post("/admin/rooms/add", data={
            "room_number": "999",
            "room_type": "Single Room",
            "description": "Temporary test room",
            "price": "175",
            "status": "Available",
        })
        self.assertEqual(created.status_code, 302)
        room = Room.query.filter_by(room_number="999").one()

        edited = self.client.post(f"/admin/rooms/{room.id}/edit", data={
            "room_number": "998",
            "room_type": "Double Room",
            "description": "Edited temporary room",
            "price": "245",
            "status": "Reserved",
        })
        self.assertEqual(edited.status_code, 302)
        self.assertEqual(room.room_number, "998")
        self.assertEqual(room.price, 245)

        deleted = self.client.get(f"/admin/rooms/{room.id}/delete")
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(db.session.get(Room, room.id))

    def test_booking_confirmation_returns_home_instead_of_viewing_status(self):
        booking = Booking(
            reference_number="NIS-HOME",
            guest_name="Home Guest",
            email="home@example.com",
            phone="0210000001",
            check_in="2030-02-10",
            check_out="2030-02-12",
            adults=1,
            children=0,
            total_price=149,
            status="Confirmed",
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add(Accounting(
            transaction_no="TXN-HOME",
            booking_id=booking.id,
            check_in=booking.check_in,
            check_out=booking.check_out,
            total_price=booking.total_price,
            payment_status="Paid",
            payment_method="Card",
        ))
        db.session.commit()

        page = self.client.get("/booking-success/NIS-HOME").get_data(as_text=True)

        self.assertIn("GO BACK HOME", page)
        self.assertNotIn("VIEW STATUS", page)

    def test_print_styles_hide_public_header_and_footer(self):
        booking_response = self.client.get("/static/css/booking.css")
        guest_flow_response = self.client.get("/static/css/guest_flow.css")
        booking_css = booking_response.get_data(as_text=True)
        guest_flow_css = guest_flow_response.get_data(as_text=True)
        booking_response.close()
        guest_flow_response.close()

        self.assertRegex(booking_css, r"@media print[\s\S]*\.footer,[\s\S]*\.topbar,")
        self.assertRegex(guest_flow_css, r"@media print[\s\S]*\.footer,")

    def test_login_success_failure_inactive_user_and_logout(self):
        success = self._login("admin", "admin-pass")
        self.assertEqual(success.status_code, 302)
        self.assertTrue(success.headers["Location"].endswith("/admin/dashboard"))

        logout = self.client.post("/auth/logout", follow_redirects=False)
        self.assertEqual(logout.status_code, 302)

        wrong_password = self._login("admin", "wrong-password")
        self.assertEqual(wrong_password.status_code, 200)
        self.assertIn(b"Invalid username or password", wrong_password.data)

        inactive = self._login("inactive", "inactive-pass")
        self.assertEqual(inactive.status_code, 200)
        self.assertIn(b"Invalid username or password", inactive.data)

    def test_unauthenticated_admin_access_redirects_to_login(self):
        response = self.client.get("/admin/dashboard", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/auth/staff-login"))

    def test_staff_and_manager_role_boundaries(self):
        self._login("staff", "staff-pass")
        self.assertEqual(self.client.get("/admin/bookings").status_code, 200)
        denied_staff = self.client.get("/admin/reports", follow_redirects=False)
        self.assertEqual(denied_staff.status_code, 302)
        self.assertTrue(denied_staff.headers["Location"].endswith("/admin/access-denied"))

        self.client.post("/auth/logout")
        self._login("manager", "manager-pass")
        self.assertEqual(self.client.get("/admin/reports").status_code, 200)
        denied_manager = self.client.get("/admin/bookings", follow_redirects=False)
        self.assertEqual(denied_manager.status_code, 302)
        self.assertTrue(denied_manager.headers["Location"].endswith("/admin/access-denied"))

    def test_authenticated_admin_smoke_pages_reach_the_requested_page(self):
        self._login("admin", "admin-pass")
        pages = [
            "/admin/dashboard",
            "/admin/inventory",
            "/admin/equipment",
            "/admin/activity-log",
            "/admin/rooms",
            "/admin/bookings",
            "/admin/payments",
            "/admin/reports",
            "/admin/walk-in-booking",
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page, follow_redirects=False)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.request.path, page)

    def test_key_pages_do_not_reference_missing_local_assets(self):
        self._login("admin", "admin-pass")
        pages = [
            "/",
            "/auth/staff-login",
            "/available-rooms",
            "/admin/dashboard",
            "/admin/walk-in-booking",
        ]

        for page in pages:
            page_response = self.client.get(page)
            self.assertEqual(page_response.status_code, 200)
            asset_urls = set(re.findall(
                r'(?:href|src)="(/static/[^"]+)"',
                page_response.get_data(as_text=True),
            ))

            for asset_url in asset_urls:
                with self.subTest(page=page, asset=asset_url):
                    asset_response = self.client.get(asset_url)
                    try:
                        self.assertEqual(asset_response.status_code, 200)
                    finally:
                        asset_response.close()


if __name__ == "__main__":
    unittest.main()
