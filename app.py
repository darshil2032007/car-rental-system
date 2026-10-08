# Car Rental Management System
# Demonstrates: Streamlit UI, Exception Handling, OOP, DB Integration, Pandas, and Matplotlib
import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st

from features import database, validators, exceptions, file_handler, reports
from features.booking_service import RentalService

# Configure Streamlit page layout and title
st.set_page_config(
    page_title="Car Rental Management System",
    page_icon="🚗",
    layout="wide"
)

# Startup: Initialize database tables once
try:
    database.create_tables()
except Exception as e:
    st.error(
        "⚠️ Database connection failed!\n\n"
        "Please check your MySQL configuration settings:\n"
        "• DB_HOST\n"
        "• DB_PORT\n"
        "• DB_USER\n"
        "• DB_PASSWORD\n"
        "• DB_NAME\n"
        "• DB_SSL (set to 'true' for cloud providers like Aiven)\n\n"
        f"Error details: {type(e).__name__}: {e}"
    )
    st.stop()

# Instantiate the single RentalService object for business operations
service = RentalService()


# ---------------- PAGE 1: DASHBOARD ----------------
def page_dashboard():
    """Displays key rental metrics and visual revenue analytics."""
    st.title("🚗 Car Rental Management Dashboard")
    st.write("Overview of fleet, bookings, and financial performance.")

    try:
        vehicles = database.get_all_vehicles()
        available_vehicles = database.get_available_vehicles()
        bookings = database.get_all_bookings()

        total_vehicles = len(vehicles)
        total_available = len(available_vehicles)

        # Active bookings have return_date as None (index 5)
        active_bookings = sum(1 for b in bookings if b[5] is None)

        # Total revenue for closed bookings (total_amount already includes late fee)
        total_revenue = sum(float(b[6]) for b in bookings if b[5] is not None)

        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Fleet", total_vehicles)
        col2.metric("Available Vehicles", total_available)
        col3.metric("Active Rentals", active_bookings)
        col4.metric("Total Revenue", f"₹{total_revenue:,.2f}")

        st.divider()
        st.subheader("📊 Revenue & Fleet Analytics")

        # Load bookings DataFrame for analytics charts
        df = reports.load_bookings_dataframe()

        if df.empty:
            st.info("No bookings recorded yet. Revenue trends and vehicle analytics will appear here once bookings are placed.")
        else:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.write("**Monthly Revenue Trend**")
                fig_rev = reports.plot_monthly_revenue(df)
                if fig_rev:
                    st.pyplot(fig_rev)
                else:
                    st.info("No completed rentals with revenue to plot yet.")

            with col_chart2:
                st.write("**Most Rented Vehicles**")
                fig_top = reports.plot_top_vehicles(df)
                if fig_top:
                    st.pyplot(fig_top)
                else:
                    st.info("No vehicle rental frequency data to plot.")

            # Fleet Category Distribution & Summary Table
            fig_pie = reports.plot_category_pie()
            if fig_pie:
                st.divider()
                col_pie1, col_pie2 = st.columns([1, 1])
                with col_pie1:
                    st.write("**Vehicle Fleet by Category**")
                    st.pyplot(fig_pie)
                with col_pie2:
                    st.write("**Monthly Revenue Summary**")
                    rev_table = reports.monthly_revenue(df)
                    if not rev_table.empty:
                        st.dataframe(rev_table, use_container_width=True)
                    else:
                        st.info("No revenue summary available.")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")


# ---------------- PAGE 2: ADD VEHICLE ----------------
def page_add_vehicle():
    """Form to add a new vehicle, update rental rate, or delete a vehicle."""
    st.title("🚙 Vehicle Management")

    st.subheader("Add New Vehicle to Fleet")
    with st.form("add_vehicle_form"):
        col1, col2 = st.columns(2)
        with col1:
            brand = st.text_input("Brand", placeholder="e.g. Maruti, Hyundai, Tata").strip()
            model = st.text_input("Model", placeholder="e.g. Swift, Creta, Nexon").strip()
        with col2:
            category = st.selectbox("Category", ["Hatchback", "Sedan", "SUV", "Bike"])
            rate = st.number_input("Rate per Day (₹)", min_value=0.0, value=1500.0, step=100.0)

        submitted = st.form_submit_button("Add Vehicle")

        if submitted:
            if not brand or not model:
                st.error("Please enter both Brand and Model.")
            else:
                try:
                    # Validate rate with assert in validators
                    validators.validate_rate(rate)
                    new_id = database.add_vehicle(brand, model, category, rate)
                    st.success(f"Vehicle '{brand} {model}' ({category}) added successfully with ID #{new_id}!")
                except AssertionError as ae:
                    st.error(f"Validation Error: {ae}")
                except Exception as e:
                    st.error(f"Error saving vehicle: {e}")

    st.divider()

    # Show existing vehicles table
    try:
        all_vehicles = database.get_all_vehicles()
        if all_vehicles:
            df = pd.DataFrame(all_vehicles, columns=["ID", "Brand", "Model", "Category", "Rate/Day (₹)", "Status"])
            st.subheader("Current Fleet Inventory")
            st.dataframe(df, use_container_width=True)

            # Update Rate and Delete Vehicle sections
            col_update, col_delete = st.columns(2)

            with col_update:
                st.subheader("Update Vehicle Daily Rate")
                vehicle_options = {f"#{v[0]} - {v[1]} {v[2]} (₹{v[4]}/day)": v[0] for v in all_vehicles}
                selected_v = st.selectbox("Select Vehicle to Update", list(vehicle_options.keys()), key="update_sel")
                new_rate = st.number_input("New Daily Rate (₹)", min_value=1.0, value=2000.0, step=100.0, key="new_rate")
                if st.button("Update Rate"):
                    try:
                        v_id = vehicle_options[selected_v]
                        database.update_vehicle_rate(v_id, new_rate)
                        st.success(f"Rate updated successfully to ₹{new_rate}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating rate: {e}")

            with col_delete:
                st.subheader("Delete Vehicle")
                delete_options = {f"#{v[0]} - {v[1]} {v[2]} ({v[5]})": v[0] for v in all_vehicles}
                selected_del = st.selectbox("Select Vehicle to Delete", list(delete_options.keys()), key="del_sel")
                if st.button("Delete Vehicle", type="primary"):
                    try:
                        v_id = delete_options[selected_del]
                        database.delete_vehicle(v_id)
                        st.success("Vehicle deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cannot delete vehicle (it may be linked to bookings): {e}")
        else:
            st.info("No vehicles in database yet.")
    except Exception as e:
        st.error(f"Error fetching vehicles: {e}")


# ---------------- PAGE 3: REGISTER CUSTOMER ----------------
def page_register_customer():
    """Form to register a new customer with regex validations."""
    st.title("👤 Register Customer")

    with st.form("register_customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. Aarav Patel").strip()
            phone = st.text_input("Phone Number (10 digits)", placeholder="e.g. 9876543210").strip()
        with col2:
            email = st.text_input("Email Address", placeholder="e.g. aarav@gmail.com").strip()
            license_no = st.text_input("Driving License No (15 chars)", placeholder="e.g. GJ0120230012345").strip().upper()

        submitted = st.form_submit_button("Register Customer")

        if submitted:
            if not (name and phone and email and license_no):
                st.error("All fields are required.")
            else:
                try:
                    # Validate inputs using regex in validators module
                    validators.validate_phone(phone)
                    validators.validate_email(email)
                    validators.validate_license(license_no)

                    cust_id = database.add_customer(name, phone, email, license_no)
                    st.success(f"Customer '{name}' registered successfully with ID #{cust_id}!")
                except exceptions.InvalidPhoneError as pe:
                    st.error(f"Phone Validation Failed: {pe}")
                except exceptions.InvalidLicenseError as le:
                    st.error(f"License Validation Failed: {le}")
                except ValueError as ve:
                    st.error(f"Email Validation Failed: {ve}")
                except Exception as e:
                    st.error(f"Registration Failed: {e}")

    st.divider()
    st.subheader("Registered Customers")
    try:
        customers = database.get_all_customers()
        if customers:
            df = pd.DataFrame(customers, columns=["Customer ID", "Name", "Phone", "Email", "License No"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No registered customers found.")
    except Exception as e:
        st.error(f"Error loading customers: {e}")


# ---------------- PAGE 4: BOOK VEHICLE ----------------
def page_book_vehicle():
    """Books an available vehicle for a customer with date checks and rent estimation."""
    st.title("🔑 Book a Vehicle")

    try:
        customers = database.get_all_customers()
        available_vehicles = database.get_available_vehicles()

        if not customers:
            st.warning("No customers registered yet. Please register a customer first.")
            return

        if not available_vehicles:
            st.warning("No vehicles are currently Available for booking.")
            return

        # Prepare selectbox options
        customer_options = {f"#{c[0]}: {c[1]} (Phone: {c[2]})": c[0] for c in customers}
        # Formatted vehicle names via service method
        vehicle_options = {f"#{v[0]}: {v[1]} {v[2]} [{v[3]}] - ₹{v[4]}/day": v for v in available_vehicles}

        col1, col2 = st.columns(2)
        with col1:
            selected_customer_label = st.selectbox("Select Customer", list(customer_options.keys()))
            selected_customer_id = customer_options[selected_customer_label]

        with col2:
            selected_vehicle_label = st.selectbox("Select Available Vehicle", list(vehicle_options.keys()))
            selected_vehicle_data = vehicle_options[selected_vehicle_label]
            selected_vehicle_id = selected_vehicle_data[0]
            vehicle_category = selected_vehicle_data[3]
            vehicle_rate = float(selected_vehicle_data[4])

        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("Start Date", value=date.today(), min_value=date.today())
        with col_date2:
            due_date = st.date_input("Due Date", value=date.today() + timedelta(days=2), min_value=date.today())

        # Rent Estimation calculation display
        if due_date >= start_date:
            est_days = max(1, (due_date - start_date).days)
            # Apply subclass multiplier for estimation
            multipliers = {"Hatchback": 1.0, "Sedan": 1.2, "SUV": 1.5, "Bike": 0.8}
            multiplier = multipliers.get(vehicle_category, 1.0)
            est_rent = round(est_days * vehicle_rate * multiplier, 2)
            st.info(f"💡 Estimated Rent for {est_days} day(s) ({vehicle_category} multiplier {multiplier}x): **₹{est_rent:,.2f}**")
        else:
            st.error("Due date cannot be before start date.")

        if st.button("Confirm Booking", type="primary"):
            try:
                booking_id = service.book_vehicle(selected_customer_id, selected_vehicle_id, start_date, due_date)
                st.success(f"🎉 Booking #{booking_id} successfully created! Vehicle is now marked as 'Booked'.")
            except exceptions.VehicleNotAvailableError as ve:
                st.error(f"Booking Error: {ve}")
            except exceptions.CustomerNotFoundError as ce:
                st.error(f"Booking Error: {ce}")
            except exceptions.InvalidDatesError as de:
                st.error(f"Booking Error: {de}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    except Exception as e:
        st.error(f"Error loading booking interface: {e}")


# ---------------- PAGE 5: RETURN VEHICLE ----------------
def page_return_vehicle():
    """Processes vehicle return, calculates charges and late fees, and generates receipt."""
    st.title("🏁 Return Vehicle & Generate Receipt")

    try:
        all_bookings = database.get_all_bookings()
        # Active bookings: return_date (index 5) is None
        active_bookings = [b for b in all_bookings if b[5] is None]

        if not active_bookings:
            st.info("No active rentals currently in progress.")
            return

        booking_options = {
            f"Booking #{b[0]} - {b[8]} ({b[9]} {b[10]}) | Due: {b[4]}": b[0]
            for b in active_bookings
        }

        col1, col2 = st.columns(2)
        with col1:
            selected_label = st.selectbox("Select Active Booking to Return", list(booking_options.keys()))
            selected_booking_id = booking_options[selected_label]
        with col2:
            return_date = st.date_input("Actual Return Date", value=date.today())

        if st.button("Process Return & Bill", type="primary"):
            try:
                # Process return through service
                bill = service.return_vehicle(selected_booking_id, return_date)

                st.success("Vehicle returned successfully! Booking closed.")

                # Billing summary display
                col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                col_b1.metric("Days Used", f"{bill['days_used']} day(s)")
                col_b2.metric("Base Rent", f"₹{bill['base_rent']:,.2f}")
                col_b3.metric("Late Penalty", f"₹{bill['late_fee']:,.2f}", delta=f"{bill['extra_days']} extra days", delta_color="inverse")
                col_b4.metric("Total Payable", f"₹{bill['total_amount']:,.2f}")

                # Generate receipt file using with statement
                receipt_path = file_handler.generate_receipt(bill)
                receipt_content = file_handler.read_receipt(bill['booking_id'])

                st.subheader("📄 Printed Receipt")
                st.text(receipt_content)

                # Download button for receipt
                st.download_button(
                    label="📥 Download Receipt (.txt)",
                    data=receipt_content,
                    file_name=f"receipt_{bill['booking_id']}.txt",
                    mime="text/plain"
                )

            except exceptions.InvalidDatesError as de:
                st.error(f"Date Error: {de}")
            except Exception as e:
                st.error(f"Error processing return: {e}")

    except Exception as e:
        st.error(f"Error loading return page: {e}")


# ---------------- PAGE: ALL BOOKINGS ----------------
def page_all_bookings():
    """Displays all rental bookings with customer/vehicle details, status filtering, and search."""
    st.title("📋 All Bookings")
    st.write("Complete history of all vehicle rental records.")

    try:
        bookings = database.get_all_bookings()

        if not bookings:
            st.info("No bookings recorded in the system yet.")
            return

        # Construct DataFrame with readable customer and vehicle names
        data = []
        for b in bookings:
            # b[5] is return_date; Active if empty/None, Returned otherwise
            is_returned = b[5] is not None and str(b[5]).strip() != "" and str(b[5]).lower() != "none"
            status = "Returned" if is_returned else "Active"
            vehicle_name = f"{b[9]} {b[10]} ({b[11]})"
            data.append({
                "Booking ID": b[0],
                "Customer Name": b[8],
                "Vehicle": vehicle_name,
                "Start Date": str(b[3]),
                "Due Date": str(b[4]),
                "Return Date": str(b[5]) if is_returned else "—",
                "Total (₹)": float(b[6]),
                "Late Fee (₹)": float(b[7]),
                "Status": status
            })

        df = pd.DataFrame(data)

        # Filters above the table
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Returned"])
        with col2:
            search_name = st.text_input("Search by Customer Name", placeholder="Type customer name...").strip()

        # Apply status filter
        filtered_df = df
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["Status"] == status_filter]

        # Apply customer name search filter
        if search_name:
            filtered_df = filtered_df[filtered_df["Customer Name"].str.contains(search_name, case=False, na=False)]

        # Display results or info message
        if filtered_df.empty:
            st.info("No bookings match the selected criteria.")
        else:
            st.dataframe(filtered_df, use_container_width=True)

            # CSV Download Button
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Bookings (CSV)",
                data=csv_data,
                file_name="all_bookings.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error loading bookings: {e}")


# ---------------- PAGE: AVAILABLE VEHICLES ----------------
def page_available_vehicles():
    """Lists available vehicles with an optional maximum daily rate filter."""
    st.title("🚗 Available Vehicles")

    max_rate = st.number_input(
        "Filter by Maximum Daily Rate (₹) [0 means no filter]:",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    try:
        # Use lambda and filter() via service method
        rate_filter = max_rate if max_rate > 0 else None
        available = service.get_available_vehicles(max_rate=rate_filter)

        if available:
            df = pd.DataFrame(available, columns=["ID", "Brand", "Model", "Category", "Rate/Day (₹)", "Status"])
            st.success(f"Found {len(available)} available vehicle(s).")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No vehicles match the selected criteria.")
    except Exception as e:
        st.error(f"Error fetching available vehicles: {e}")


# ---------------- PAGE 7: OVERDUE REPORT ----------------
def page_overdue_report():
    """Lists overdue active rentals using Python generator function."""
    st.title("⚠️ Overdue Rentals Report")
    st.write("Demonstrates Python generator function (yield) to stream overdue bookings.")

    check_date = st.date_input("Check Overdue As Of Date", value=date.today())

    try:
        # Consume generator get_overdue_bookings
        overdue_generator = service.get_overdue_bookings(today=check_date)
        overdue_list = list(overdue_generator)

        if overdue_list:
            st.warning(f"⚠️ {len(overdue_list)} booking(s) are currently OVERDUE!")
            df = pd.DataFrame(overdue_list, columns=[
                "Booking ID", "Customer ID", "Vehicle ID", "Start Date", "Due Date",
                "Return Date", "Total (₹)", "Late Fee (₹)", "Customer Name",
                "Brand", "Model", "Category"
            ])
            display_cols = ["Booking ID", "Customer Name", "Brand", "Model", "Category", "Start Date", "Due Date"]
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.success("✅ No overdue bookings! All active rentals are within their scheduled due dates.")
    except Exception as e:
        st.error(f"Error generating overdue report: {e}")


# ---------------- NAVIGATION ROUTER ----------------
def main():
    st.sidebar.title("🚘 Car Rental Menu")
    menu = [
        "Dashboard",
        "Add Vehicle",
        "Register Customer",
        "Book Vehicle",
        "Return Vehicle",
        "All Bookings",
        "Available Vehicles",
        "Overdue Report"
    ]
    choice = st.sidebar.radio("Select Navigation", menu)

    # Simple page router using if/elif
    if choice == "Dashboard":
        page_dashboard()
    elif choice == "Add Vehicle":
        page_add_vehicle()
    elif choice == "Register Customer":
        page_register_customer()
    elif choice == "Book Vehicle":
        page_book_vehicle()
    elif choice == "Return Vehicle":
        page_return_vehicle()
    elif choice == "All Bookings":
        page_all_bookings()
    elif choice == "Available Vehicles":
        page_available_vehicles()
    elif choice == "Overdue Report":
        page_overdue_report()


if __name__ == "__main__":
    main()
