# Marts Documentation

## Overview
The Marts layer follows a Star Schema design tailored for the Medical Warehouse analytics.

## Models
*   **fct_messages**: The central fact table containing individual message events, view counts, and text metrics.
*   **dim_channels**: Dimension table capturing channel metadata and aggregate statistics per channel.
*   **dim_dates**: A standard date dimension to facilitate time-series analysis and cohorting by day/week/month.
