# ─────────────────────────────────────────────
# 8. DETAIL VIEW (Updated for Uniform Candles & Correct Labels)
# ─────────────────────────────────────────────
if st.session_state.selected_stock is not None:
    ticker       = st.session_state.selected_stock
    clean_sym    = ticker.replace(".NS","").replace("-USD","")
    display_name = NAME_MAP.get(ticker, clean_sym)

    # Back + breadcrumb
    col_back, col_bread = st.columns([1, 8])
    with col_back:
        if st.button("← Markets", key="back_btn"):
            st.session_state.selected_stock = None
            st.rerun()
    with col_bread:
        st.markdown(
            f'<div class="breadcrumb" style="padding-top:9px">'
            f'Markets &nbsp;/&nbsp; <span>{clean_sym}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="detail-header">'
        f'  <div class="detail-symbol">{clean_sym}</div>'
        f'  <div style="font-family:var(--sans);font-size:.88rem;color:#4e5a6e">{display_name}</div>'
    f'</div>',
        unsafe_allow_html=True
    )

    # Timeframe tabs - Mapped to your specific course-of-time logic
    tf_keys   = list(TIME_SETTINGS.keys())
    tf_labels = [TIME_SETTINGS[k]["label"] for k in tf_keys]
    tabs      = st.tabs(tf_labels)

    for i, tab in enumerate(tabs):
        with tab:
            cfg      = TIME_SETTINGS[tf_keys[i]]
            df_chart = fetch_detail_data(ticker, cfg["period"], cfg["interval"])
            df_ai    = fetch_detail_data(ticker, "1d", "1m")

            if df_chart.empty:
                st.warning(f"No data available for {ticker}.")
                continue

            # --- CANDLESTICK VISUAL FIXES ---
            fig = go.Figure(data=[go.Candlestick(
                x=df_chart.index,
                open=df_chart["Open"],  high=df_chart["High"],
                low=df_chart["Low"],    close=df_chart["Close"],
                increasing_line_color="#3fb950", increasing_fillcolor="#1a3320",
                decreasing_line_color="#f85149", decreasing_fillcolor="#3a1010",
                line=dict(width=1.2), # Slightly thicker lines for clarity
            )])

            # FIX 1: Remove gaps & fix thickness using 'category' type for Intraday/Hourly
            # This forces Plotly to treat every candle as an equal 'slot' regardless of time gaps
            if tf_keys[i] in ("1m", "1h"):
                fig.update_xaxes(
                    type='category', 
                    tickangle=0,
                    nticks=10, # Keeps the bottom labels clean
                    gridcolor="#1c2333"
                )
            else:
                # For Daily/Monthly, we use standard date but hide weekends
                fig.update_xaxes(
                    rangebreaks=[dict(bounds=["sat", "mon"])],
                    gridcolor="#1c2333"
                )

            fig.update_layout(
                template="plotly_dark", height=500,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#07090f",
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis_rangeslider_visible=False,
                font=CHART_FONT,
                yaxis=dict(
                    gridcolor="#1c2333", 
                    linecolor="#1c2333",
                    tickfont=CHART_FONT, 
                    showgrid=True, 
                    side="right",
                    fixedrange=False # Allows vertical scaling
                ),
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            # --- INTRADAY METRICS & AI ---
            if not df_ai.empty:
                op   = float(df_ai["Open"].iloc[0])
                curr = float(df_ai["Close"].iloc[-1])
                ts   = df_ai.index[-1]
                pct  = (curr - op) / op * 100
                vol  = df_ai["Close"].pct_change().dropna().std()
                up   = curr >= op
                cc   = "up" if up else "down"
                cs   = "+" if up else ""

                st.markdown(f"""
                <div class="metric-strip">
                  <div class="metric-cell">
                    <div class="metric-label">Open</div>
                    <div class="metric-value">${op:,.2f}</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Last Price</div>
                    <div class="metric-value">${curr:,.2f}</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Day Change</div>
                    <div class="metric-value {cc}">{cs}{pct:.2f}%</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Intraday Volatility</div>
                    <div class="metric-value">{vol*100:.3f}%</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if not np.isnan(vol) and vol > 0:
                    bull, base, bear = run_monte_carlo(curr, vol)
                    if ticker not in st.session_state.morning_predictions:
                        st.session_state.morning_predictions[ticker] = base
                    eod   = st.session_state.morning_predictions[ticker]
                    trend = "advance toward" if eod > op else "decline toward"

                    st.markdown(f"""
                    <div class="insight-strip">
                        Opened at <b>${op:,.2f}</b>. Volatility model projects the instrument 
                        to <b>{trend} ${eod:,.2f}</b> by close.
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Bull scenario: <b>${bull:,.2f}</b>
                        &nbsp;&nbsp;·&nbsp;&nbsp;
                        Bear scenario: <b>${bear:,.2f}</b>
                    </div>
                    """, unsafe_allow_html=True)

                    is_eod = (
                        (ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 25) or
                        (not ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 55)
                    )
                    if is_eod:
                        diff = curr - eod
                        acc  = 100 - abs(diff) / eod * 100
                        st.markdown(f"""
                        <div class="eod-report">
                        CLOSING REPORT — {clean_sym}<br>
                        ─────────────────────────────<br>
                        Predicted Close &nbsp;&nbsp;&nbsp; ${eod:,.2f}<br>
                        Actual Close &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${curr:,.2f}<br>
                        Difference &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${diff:+,.2f}<br>
                        Model Accuracy &nbsp;&nbsp;&nbsp; {acc:.2f}%
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("Awaiting sufficient intraday data.")

    st.markdown('<div class="mp-footer">Market Pulse &nbsp;·&nbsp; Data via Yahoo Finance &nbsp;·&nbsp; For informational use only. Not financial advice.</div>', unsafe_allow_html=True)
    st.stop()
