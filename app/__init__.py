# import requests
# from lxml import html
#
# # Step 1: Set up the session for handling cookies and authorization
# session = requests.Session()
#
# # Yandex login URL
# login_url = "https://passport.yandex.com/auth"
#
# application.bot_data['YANDEX_OAUTH'] = os.environ['YANDEX_OAUTH']
# application.bot_data['YANDEX_COOKIE'] = os.environ['YANDEX_COOKIE']
# application.bot_data['DEVELOPER_CHAT_ID'] = os.environ['DEVELOPER_CHAT_ID']
#
# # Credentials
# payload = {
#     'login': 'hnkovr',  # Replace with your Yandex login
#     'passwd': 'your_password'  # Replace with your Yandex password
# }
#
# # Step 2: Perform login
# response = session.post(login_url, data=payload)
#
# # Ensure login was successful (You might need to adjust this based on Yandex's login response)
# if response.ok:
#     print("Logged in successfully.")
#
#     # Step 3: Access the target page after login
#     page_url = 'https://your_target_page.com'  # Replace with your target URL
#     response = session.get(page_url)
#
#     if response.ok:
#         # Parse the HTML content
#         tree = html.fromstring(response.content)
#
#         # Step 4: Extract data using XPath
#         h2_elements = tree.xpath('/html/body/div[1]/div[1]/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/div/ul/li/div/h2')
#         ul_elements = tree.xpath('/html/body/div[1]/div[1]/div[2]/div/div/div[3]/div[1]/div[3]/div[2]/div/ul/li/div/ul')
#
#         # Step 5: Print extracted data
#         for h2 in h2_elements:
#             print(f"H2 Element: {h2.text_content().strip()}")
#
#         for ul in ul_elements:
#             print(f"UL Element: {ul.text_content().strip()}")
#     else:
#         print(f"Failed to retrieve the target page. Status code: {response.status_code}")
# else:
#     print("Login failed.")
#
