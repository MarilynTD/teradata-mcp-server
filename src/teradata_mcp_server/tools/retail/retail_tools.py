from teradatasql import TeradataConnection


def handle_retail_rfmAnalysis(
    conn: TeradataConnection,
    database: str = "DEMO_Retail",
    table: str = "UK_Retail_Data",
    mode: str = "summary",
):
    """
    Executes a full RFM (Recency, Frequency, Monetary) analysis in-database on a retail
    transactions table. Segments customers into strategic groups based on their purchase behavior.

    PARAMETERS:
        database:
            Optional Argument.
            Name of the Teradata database containing the transactions table.
            Default: "DEMO_Retail"
            Types: str

        table:
            Optional Argument.
            Name of the transactions table. Must contain columns:
            CustomerID, InvoiceDate, InvoiceNo, Quantity, UnitPrice.
            Default: "UK_Retail_Data"
            Types: str

        mode:
            Optional Argument.
            Controls the level of detail returned.
            "summary" returns aggregated metrics per RFM segment (recommended for dashboards).
            "detail"  returns one row per customer with individual R, F, M scores and segment.
            Default: "summary"
            Types: str

    RETURNS:
        list[dict] — rows with RFM metrics and segment labels.

    SEGMENTS:
        Champions       — Recent, frequent, high-spend customers. Reward and retain.
        Clientes Leales — Regular buyers. Upsell and loyalty programs.
        Nuevos Clientes — Recent first-time buyers. Drive second purchase.
        Potencial Leal  — Recent with good spend. Increase frequency.
        En Riesgo       — Previously frequent, now inactive. Urgent reactivation.
        No Perder       — High historical value, now inactive. VIP win-back offer.
        Hibernando      — No recent activity, low frequency. Win-back campaign.
        Necesita Atencion — Mixed metrics. Case-by-case analysis.
    """
    full_table = f"{database}.{table}"

    rfm_sql = f"""
    WITH base AS (
        SELECT
            CustomerID,
            MAX(CAST(InvoiceDate AS DATE))  AS UltimaCompra,
            COUNT(DISTINCT InvoiceNo)       AS Frecuencia,
            SUM(Quantity * UnitPrice)       AS Monetario
        FROM {full_table}
        WHERE Quantity > 0
          AND CustomerID IS NOT NULL
        GROUP BY CustomerID
    ),
    referencia AS (
        SELECT MAX(CAST(InvoiceDate AS DATE)) AS FechaRef
        FROM {full_table}
    ),
    rfm_scores AS (
        SELECT
            b.CustomerID,
            CAST((r.FechaRef - b.UltimaCompra DAY(4)) AS INTEGER) AS Recencia_Dias,
            b.Frecuencia,
            CAST(b.Monetario AS DECIMAL(12,2))                     AS Monetario,
            CASE
                WHEN (r.FechaRef - b.UltimaCompra DAY(4)) <= 30  THEN 5
                WHEN (r.FechaRef - b.UltimaCompra DAY(4)) <= 60  THEN 4
                WHEN (r.FechaRef - b.UltimaCompra DAY(4)) <= 90  THEN 3
                WHEN (r.FechaRef - b.UltimaCompra DAY(4)) <= 180 THEN 2
                ELSE 1
            END AS R_Score,
            CASE
                WHEN b.Frecuencia >= 20 THEN 5
                WHEN b.Frecuencia >= 10 THEN 4
                WHEN b.Frecuencia >= 5  THEN 3
                WHEN b.Frecuencia >= 2  THEN 2
                ELSE 1
            END AS F_Score,
            CASE
                WHEN b.Monetario >= 5000 THEN 5
                WHEN b.Monetario >= 2000 THEN 4
                WHEN b.Monetario >= 1000 THEN 3
                WHEN b.Monetario >= 500  THEN 2
                ELSE 1
            END AS M_Score
        FROM base b CROSS JOIN referencia r
    ),
    rfm_segmented AS (
        SELECT
            CustomerID,
            Recencia_Dias,
            Frecuencia,
            Monetario,
            R_Score,
            F_Score,
            M_Score,
            (R_Score + F_Score + M_Score) AS RFM_Total,
            CASE
                WHEN R_Score >= 4 AND F_Score >= 4 AND M_Score >= 4 THEN 'Champions'
                WHEN R_Score >= 3 AND F_Score >= 3                  THEN 'Clientes Leales'
                WHEN R_Score >= 4 AND F_Score <= 2                  THEN 'Nuevos Clientes'
                WHEN R_Score >= 3 AND F_Score >= 1 AND M_Score >= 3 THEN 'Potencial Leal'
                WHEN R_Score <= 2 AND F_Score >= 3 AND M_Score >= 3 THEN 'En Riesgo'
                WHEN R_Score <= 2 AND F_Score >= 4 AND M_Score >= 4 THEN 'No Perder'
                WHEN R_Score <= 2 AND F_Score <= 2                  THEN 'Hibernando'
                ELSE 'Necesita Atencion'
            END AS Segmento_RFM
        FROM rfm_scores
    )
    """

    if mode == "summary":
        sql = rfm_sql + """
    SELECT
        Segmento_RFM,
        COUNT(*)                                     AS Total_Clientes,
        CAST(AVG(Monetario)     AS DECIMAL(10,2))    AS Ticket_Promedio_GBP,
        CAST(SUM(Monetario)     AS DECIMAL(12,2))    AS Ingresos_Totales_GBP,
        CAST(AVG(Recencia_Dias) AS DECIMAL(6,1))     AS Recencia_Promedio_Dias,
        CAST(AVG(Frecuencia)    AS DECIMAL(6,1))     AS Frecuencia_Promedio
    FROM rfm_segmented
    GROUP BY Segmento_RFM
    ORDER BY Ingresos_Totales_GBP DESC
    """
    else:
        sql = rfm_sql + """
    SELECT
        CustomerID,
        Recencia_Dias,
        Frecuencia,
        Monetario,
        R_Score,
        F_Score,
        M_Score,
        RFM_Total,
        Segmento_RFM
    FROM rfm_segmented
    ORDER BY RFM_Total DESC
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return [dict(zip(columns, row)) for row in rows]
