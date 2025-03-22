# This module contains the extra HTML, CSS code which beautifies the app!

import streamlit as st

def custom_header(
    header_p_html_id:str="header_text",
    header_text_align:str="center",
    header_text:str="InformatIQ 💡",
    font_size_default_rem:str="4",
    font_size_max_768p:str="3",
    font_size_max_480p:str="2"
) -> None:

    """
    Custom Header with a sparkle of CSS!
    """

    header_html = f"""
        <p id="{header_p_html_id}" style="text-align: {header_text_align};">
            {header_text}
        </p>
        <style>
            #{header_p_html_id} {{
                font-size: {font_size_default_rem}rem;
            }}

            @media (max-width: 768px) {{
                    #{header_p_html_id} {{
                        font-size: {font_size_max_768p}rem;
                    }}
            }}

            @media (max-width: 480px) {{
                #{header_p_html_id} {{
                    font-size: {font_size_max_480p}rem;
                }}
            }}
        </style>
    """

    st.markdown(header_html, unsafe_allow_html=True)

def sticky_bar(sticky_bar_text:str="Made with 💓 by SRH Heidelberg") -> None:

    """
    Sticky bar to display some text on the both of the app.
    """

    sticky_bar_html = f'''
        <div style = "
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            color: white;
            background-color: #262730;
            color: white;
            font-size: 12px;
            z-index: 1000;
            text-align: center;">
            {sticky_bar_text}
        </div>
    '''

    st.markdown(sticky_bar_html, unsafe_allow_html=True)

def center_button_group() -> None:
    """
    CSS to center the Button Tabs and also center normal buttons
    """

    center_button_group = '''
        <style>
            .stButtonGroup {
                display: flex;
                padding: 1rem 0;
                justify-content: center;
            }

            .stAlert {
                background: #001725;
            }

            .stHeadingDivider {
                background-color: #df4807;
            }

            div.stButton .stTooltipIcon {
                justify-content: center;
            }

            div.stButton .stTooltipHoverTarget {
                width: 15%;
            }

            .stTooltipHoverTarget > button {
                width: 100%;
            }

            .stMarkdown {
                text-align: center;
            }
            
        </style>
    '''

    st.markdown(center_button_group, unsafe_allow_html=True)

def page_link_center() -> None:

    st.markdown("""
    <style>
        .stPageLink div {
            align-items: center;
        }
            
        .stMarkdown p {
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
