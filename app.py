import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re

st.set_page_config("Uber Analytics", layout="wide")


df = pd.read_csv("Uber data set ncr.xlsx - ncr_ride_bookings.csv")

FILE_NAME = "users.csv"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Login"

if "username" not in st.session_state:
    st.session_state.username = ""


#login
def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not os.path.exists(FILE_NAME):
            st.error("No users found. Please signup first.")
            return

        df_users = pd.read_csv(FILE_NAME)

        user = df_users[
            (df_users["Username"] == username) &
            (df_users["Password"] == password)
        ]

        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Username or Password")

    if st.button("New User? Signup"):
        st.session_state.page = "Signup"
        st.rerun()


#signup
def signup():
    st.title("Signup")

    if not os.path.exists(FILE_NAME):
        dfu = pd.DataFrame(columns=["Username", "Password"])
        dfu.to_csv(FILE_NAME, index=False)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    repassword = st.text_input("Re-enter Password", type="password")

    if st.button("Signup"):
        df_users = pd.read_csv(FILE_NAME)

        if not username or not password or not repassword:
            st.error("Fill all fields")

        elif password != repassword:
            st.error("Passwords do not match")

        elif username in df_users["Username"].values:
            st.error("Username already exists")

        else:
            new_user = pd.DataFrame([{
                "Username": username,
                "Password": password
            }])

            df_users = pd.concat([df_users, new_user], ignore_index=True)
            df_users.to_csv(FILE_NAME, index=False)

            st.success("Account created successfully")
            st.session_state.page = "Login"
            st.rerun()

    if st.button("Already have account? Login"):
        st.session_state.page = "Login"
        st.rerun()


if not st.session_state.logged_in:
    if st.session_state.page == "Login":
        login()
    elif st.session_state.page == "Signup":
        signup()
    st.stop()


if st.session_state.logged_in:
    with st.sidebar:

        selected = option_menu("Main Menu",
                               ["Dataset","Overview","Ride Analytics","Data Assistant"],
                               icons=["table","bar-chart","graph-up"],
                               menu_icon="car-front",
                               default_index=0)

    if selected == "Dataset":
        st.title("Data Explorer")
        st.divider()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows", df.shape[0])
        col2.metric("Total Columns", df.shape[1])
        col3.metric("Mising Value", df.isna().sum().sum())

        st.divider()

        # column selection
        st.subheader("Select Column")
        selected_column = st.multiselect("Select Column to Display",
                                         df.columns, default=df.columns)
        filtered_df = df[selected_column]

        # search
        st.subheader("Search in Dataset")
        search_value = st.text_input("Enter Value to Search")
        if search_value:
            filtered_df = filtered_df[filtered_df.astype(str).apply(
                lambda row: row.str.contains(search_value, case=False).any(), axis=1
            )]
        # st.dataframe(filtered_df)
        st.subheader("Select Row Range")

        row_range = st.slider(
            "Choose row range",
            0,
            len(filtered_df),
            (0, min(100, len(filtered_df)))
        )
        filtered_df = filtered_df.iloc[row_range[0]:row_range[1]]
        # st.dataframe(filtered_df)

        col1, col2 = st.columns(2)

        with col1:
            selected_col = st.selectbox(
                "Select Column",
                filtered_df.columns
            )

        with col2:
            unique_values = ["All"] + list(filtered_df[selected_col].dropna().unique())

            selected_value = st.selectbox(
                "Select Value",
                unique_values
            )

        if selected_value != "All":
            filtered_df = filtered_df[filtered_df[selected_col] == selected_value]

        st.dataframe(filtered_df, use_container_width=True)

        csv = filtered_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Filtered Data",
            data=csv,
            file_name="filtered_data.csv",
            mime="text/csv"
        )

        # OVERVIEW
    if selected == "Overview":
        st.header("Ride Overview")
        completion_rate = (df["Booking Status"].value_counts().get('Completed', 0) / len(df)) * 100
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rides", len(df))
        col2.metric("Revenue", df["Booking Value"].sum())
        total_revenue = df["Booking Value"].sum()
        col3.metric("Completion Rate", f"{completion_rate:.1f}%")
        col4.metric("Avg Ride Value", f"₹{df['Booking Value'].mean():.0f}")

        st.divider()

        # business unit perfomance
        st.header("Business Unit Performance Metrix")
        bu_matrix = df.groupby("Vehicle Type").agg(
            Total_Booking=("Booking ID", "count"),
            Revenue_Generated=("Booking Value", "sum"),
            Avg_Distance=("Ride Distance", "mean"),
            Avg_Rating=("Driver Ratings", "mean")
        )

        bu_matrix["Revenue Share%"] = (bu_matrix["Revenue_Generated"]/total_revenue*100
                                       if (total_revenue)>0 else 0)

        st.dataframe(bu_matrix.style.format({
            "Revenue_Generated": "${:,.2f}",
            "Avg_Distance": "{:,.2f}km",
            "Avg_Rating": "{:,.1f}",
            "Revenue Share%": "${:,.1f}"
        }).background_gradient(subset=["Revenue_Generated"], cmap="YlOrRd"))

        # OPERATION EFEICIENCY

        col_eff, col_can = st.columns(2)
        with col_eff:
            st.header("Operational Efficiency")
            eff_df = df.groupby("Vehicle Type")[["Avg VTAT", "Avg CTAT"]].mean()
            st.write("Average Turn Around Time {%in Minutes%}")
            st.dataframe(eff_df.style.highlight_max(axis=0, color="#2bfb6b").highlight_min(axis=0, color="#fb352b"),
                         use_container_width=True)

        total_rides = len(df)
        with col_can:
            st.header("Cancellation Audit")
            status_count = df["Booking Status"].value_counts().to_frame(name="Count")
            status_count["Share %"] = (status_count["Count"] / total_rides * 100)
            st.write("Breakdown of Ride Cancellation and Completion Statu")
            st.dataframe(status_count, use_container_width=True)
            st.divider()

        completed_rides = df.groupby("Payment Method")["Booking ID"]
        st.dataframe(completed_rides)

        # Top Insights
        st.subheader("Top Insights")

        top_vehicle = df.groupby("Vehicle Type")["Booking Value"].sum().idxmax()
        top_payment = df["Payment Method"].mode()[0]

        col1, col2 = st.columns(2)

        col1.success(f"Highest Revenue Vehicle: {top_vehicle}")
        col2.info(f"Most Used Payment Method: {top_payment}")

        # FINANCIAL ANALYSIS
        st.header("Financial Deep Dive")
        pay_col, reason_col = st.columns([4, 6])
        with pay_col:
            st.markdown(" ** Payment Method Distribution")
        pay_summary = (df["Payment Method"].value_counts(normalize=True) * 100)
        st.dataframe(pay_summary)

        st.header("Completed Rides by Payment Method")
        completed_rides = df.groupby("Payment Method")["Booking ID"].count()
        completed_rides.columns = ["Payment Method", "Total Rides"]
        st.dataframe(completed_rides, use_container_width=True)

        # Data Quality
        with st.expander("Data Quality & Audit Logs"):
            audit1, audit2 = st.columns(2)
            audit1.write(f"**Duplicate Records:{df.duplicated().sum()}")
            audit2.write(f"Missing Value:{df["Booking Status"].isna().sum()}")
            st.info("Missing Booking Value are expected for cancellation and no driver acceptance")
            st.success("Executive Overview are generated from operational dataset")

        st.title("Uber Operations")
        st.markdown("---")

        # strategic kpi
        completed_rides = df[df["Booking Status"] == "Completed"]
        total_revenue = completed_rides["Booking Value"].sum()
        avg_distance = completed_rides["Ride Distance"].mean()
        success_rate = (len(completed_rides) / total_revenue * 100 if (total_revenue) > 0 else 0)
        avg_rating = completed_rides["Customer Rating"].dropna().mean()

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(f"Gross Total Revenue", f"{total_revenue:,.0f}", "target: %1.2M")
        kpi2.metric("Average Distance", f"{avg_distance:,.1f}KM")
        kpi3.metric("Fullfillment Rate", f"{success_rate:,.2f}%", "-2.4% v/s Last Month", "red")
        kpi4.metric("Average Customer Rating", f"{avg_rating:,.1f}")

        st.divider()
        # Column Statistics
        selected_cols = st.multiselect("Select Columns", df.columns)

        option = st.selectbox("Int Value", ["Int", "Float"])

        if selected_cols:
            temp_df = df[selected_cols]

            if option == "Int":
                int_data = temp_df.select_dtypes(include=['int64'])
                st.write(int_data)

            elif option == "Float":
                int_data = temp_df.select_dtypes(include=['float64'])
                st.write(int_data)

        # ride analytics
    if selected == "Ride Analytics":
        st.title("Advance Ride Intelligence Dashboard")

        completed = df[df["Booking Status"] == "Completed"]
        # sunburst chart
        st.subheader("Revenue Hierarchy")
        fig1 = px.sunburst(completed, path=["Vehicle Type", "Payment Method"],
                           values="Booking Value",
                           color="Booking Value",
                           color_continuous_scale="Turbo")
        fig1.update_layout(height=500)
        st.plotly_chart(fig1)

        # treemap
        # treemap
        st.subheader("Revenue Distribution")
        fig2 = px.treemap(completed, path=["Vehicle Type", "Payment Method"],
                          values="Booking Value",
                          color="Booking Value",
                          color_continuous_scale="Blues")
        fig2.update_layout(margin=dict(t=20, l=0, r=0, b=0), height=420)
        st.plotly_chart(fig2)

        st.subheader("Customer Rating Spread")
        fig3 = px.box(completed, x="Vehicle Type", y="Customer Rating", color="Vehicle Type")
        fig3.update_layout(showlegend=True, height=420)
        st.plotly_chart(fig3)

        # sankey diagram
        st.subheader("Ride Flow Analysis")
        flow = df.groupby(["Vehicle Type", "Booking Status"]).size().reset_index(name="Count")
        # st.dataframe(flow)
        source_label = flow["Vehicle Type"].unique().tolist()
        target_label = flow["Booking Status"].unique().tolist()

        labels = source_label + target_label

        source = flow["Vehicle Type"].apply(
            lambda x: labels.index(x))

        target = flow["Booking Status"].apply(
            lambda x: labels.index(x))

        value = flow["Count"].tolist()

        fig4 = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="blue", width=0.5), label=labels
            ),
            link=dict(source=source, target=target, value=value)
        )])
        st.plotly_chart(fig4)

        # bar
        st.subheader("Ride Demand by Vehicle Type")

        demand = df.groupby("Vehicle Type").size().reset_index(name="Total Bookings")

        fig5 = px.bar(demand, x="Vehicle Type", y="Total Bookings", color="Vehicle Type")
        st.plotly_chart(fig5, use_container_width=True)

        # horizontal bar
        st.subheader("Revenue by Vehicle Type")

        revenue = df.groupby("Vehicle Type").agg(TotalRevenue=("Booking Value", "sum")).reset_index()
        fig6 = px.bar(revenue, x="TotalRevenue", y="Vehicle Type", color="Vehicle Type")
        st.plotly_chart(fig6, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            # donut
            st.subheader("Booking Status Distribution")

            status = df.groupby("Booking Status").size().reset_index(name="Count")
            fig7 = px.pie(status, values="Count", names="Booking Status", hole=0.5)
            st.plotly_chart(fig7, use_container_width=True)
        with col2:
            # pie
            st.subheader("Payment Method Distribution")

            payment = df.groupby("Payment Method").size().reset_index(name="Count")
            fig8 = px.pie(payment, values="Count", names="Payment Method")
            st.plotly_chart(fig8, use_container_width=True)

        # scatter
        st.subheader("Ride Distance vs Booking Value")
        fig9 = px.scatter(df,
                          x="Ride Distance",
                          y="Booking Value",
                          color="Vehicle Type")
        st.plotly_chart(fig9, use_container_width=True)

        # histogram
        st.subheader("Customer Rating Distribution")
        fig10 = px.histogram(df, x="Customer Rating", nbins=20)
        st.plotly_chart(fig10, use_container_width=True)

        # horizontal bar2
        st.subheader("Cancellation Reasons Analysis")

        cancel = df[df["Booking Status"] != "Completed"]
        cancel["Cancellation Reason"] = cancel["Reason for cancelling by Customer"].fillna(
            cancel["Driver Cancellation Reason"]
        )
        cancel_ride = cancel.groupby("Cancellation Reason").size().reset_index(name="Count")
        fig11 = px.bar(cancel_ride, x="Count", y="Cancellation Reason", orientation="h", color="Cancellation Reason")
        st.plotly_chart(fig11, use_container_width=True)

        # bar3
        st.subheader(" Average Distance by Vehicle Type")
        avg_distance = df.groupby("Vehicle Type")["Ride Distance"].mean().reset_index()

        fig12 = px.bar(avg_distance,
                       x="Vehicle Type",
                       y="Ride Distance",
                       color="Vehicle Type",
                       title="Average Distance by Vehicle Type")

        st.plotly_chart(fig12, use_container_width=True)

        # histo
        st.subheader("Booking Value Distribution")
        fig13 = px.histogram(df,
                             x="Booking Value",
                             nbins=35,
                             title="Booking Value Distribution")

        st.plotly_chart(fig13, use_container_width=True)

        # scatter2
        st.subheader("Operational Efficiency (CTAT vs VTAT)")
        fig14 = px.scatter(df,
                           x="Avg CTAT",
                           y="Avg VTAT",
                           title="CTAT vs VTAT",
                           opacity=0.6)

        st.plotly_chart(fig14, use_container_width=True)

        # data asistant
    if selected == "Data Assistant":
        st.title("Data Assistant")
        st.divider()

        st.write("Ask Question about the dataset and get visual analytics")
        user_question = st.text_input("Ask Me Question")

        if user_question:
            q = user_question.lower()

            completed = df[df["Booking Status"] == 'Completed']

            # total rides
            if "total rides" in q:
                total = len(df)
                st.success(f"Total Rides in Dataset {total}")

                status = df["Booking Status"].value_counts()
                fig = px.bar(x=status.index,
                             y=status.values,
                             labels={"x": "Booking Status", "y": "Ride Count"},
                             title="Ride Distribution by Status")
                st.plotly_chart(fig, use_container_width=True)

            # revenue analysis
            elif "revenue" in q:
                revenue = completed.groupby("Vehicle Type")["Booking Value"].sum()
                st.success(f"Total Revenue: {revenue.sum():,.2f}")

                fig = px.bar(x=revenue.index,
                             y=revenue.values,
                             title="Revenue by Vehicle Type",
                             labels={"x": "Vehicle Type", "y": "Revenue"})
                st.plotly_chart(fig, use_container_width=True)

            elif "vehicle" in q:
                vehicle = df["Vehicle Type"].value_counts()
                st.success(f"Most Used Vehicle : {vehicle.idxmax()}")

                fig = px.pie(names=vehicle.index, values=vehicle.values, title="Vehicle Usage Distribution")
                st.plotly_chart(fig)



            # payment analysis
            elif "payment" in q:
                payment = completed["Payment Method"].value_counts()
                fig = px.pie(names=payment.index, values=payment.values, title="Payment Method")

                st.plotly_chart(fig)

            # cancellation
            elif "cancel" in q:
                cancel = df["Booking Status"].value_counts()
                fig = px.bar(x=cancel.index, y=cancel.values, title="Ride Status",
                             labels={"x": "Status", "y": "Ride Count"})
                st.plotly_chart(fig)

            # rating
            elif "rating" in q:
                fig = px.histogram(completed, x="Customer Rating", nbins=10, title="Customer Rating")
                st.plotly_chart(fig)
                st.success(f"Average Rating: {completed["Customer Rating"].mean():,.2f}")


            # distance

            elif "distance" in q:
                fig = px.scatter(completed, x="Ride Distance",
                                 y="Booking Value",
                                 color="Vehicle Type",
                                 title="Ride Distance by Booking Value")
                st.plotly_chart(fig)

            else:
                st.warning(
                    "Question not recognized , Try something like, cancellation, distance, revenue, rating, vehicle etc")
                st.divider()
