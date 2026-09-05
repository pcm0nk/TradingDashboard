import streamlit as st


@st.dialog("📩 Contact & Support")
def show_contact_modal():
    tab_contact, tab_donate = st.tabs(["💬 Direct Contact", "☕ Donate & Support"])

    # ── TAB 1: DIRECT CONTACT & COMMUNITY ────────────────────────────────────
    with tab_contact:
        st.markdown(
            "Have a question, feedback, bug report, or just want to chat about"
            " trading? Reach out or join the community below!"
        )
        st.markdown("---")

        # Telegram
        st.markdown("💬 **Telegram**\n\n[Chat @pc_monk](https://t.me/pc_monk)")
        st.markdown("---")

        # Discord Community & Direct Message
        st.markdown(
            "🎮 **Discord Community**\n\n"
            "[Join Discord Server](https://discord.gg/f847mFwheg)\n\n"
            "**Direct Message:** `pcmonk`"
        )
        st.markdown("---")

        # GitHub
        st.markdown(
            "🛠️ **GitHub Issues**\n\n"
            "[Open an Issue](https://github.com/pcm0nk/TradingDashboard/issues)"
        )

    # ── TAB 2: DONATION & SUPPORT ─────────────────────────────────────────────
    with tab_donate:
        st.markdown(
            "Donations help keep the project maintained and support adding new analytical features!"
        )
        st.markdown("---")

        # Vertical Row 1: Bitcoin
        st.markdown("🪙 **Bitcoin (BTC)**")
        st.code("bc1q3r4405f876lgaz8wnx3ddc2stpuem03mkzyevw", language="text")
        st.markdown("---")

        # Vertical Row 2: USDC (BSC - BEP20)
        st.markdown("💵 **USDC (BSC - BEP20)**")
        st.code("0x923eD04b7274c7db95566BeE92E42B67976c403A", language="text")
        st.markdown("---")

        # Vertical Row 3: USDT (BSC - BEP20)
        st.markdown("💵 **USDT (BSC - BEP20)**")
        st.code("0x923eD04b7274c7db95566BeE92E42B67976c403A", language="text")
        st.markdown("---")

        # Vertical Row 4: KCEX Referral
        st.markdown("📈 **Trade on KCEX**")
        st.markdown(
            "Trade with my referral link on **KCEX** for **0% fees** on both"
            " perpetual futures and spot trading:"
        )
        st.markdown(
            "👉 **[Register on KCEX (0% Fees)](https://www.kcex.com/register?inviteCode=R2ZQNQ)**"
        )
        st.markdown(
                    "Or Use Below Code:"
                )
        st.code("R2ZQNQ", language="text")

    st.markdown("---")
    if st.button("Close Window", use_container_width=True):
        st.rerun()