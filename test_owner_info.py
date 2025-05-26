import requests

# 用户手动填写cookies字符串
cookies = """
weblogger_did=web_342587182342A23; _did=web_369923319E186051; did=web_34f4f4be779ec7bbd0ef47d262263b0f1c34; bUserId=1000441953824; bUserId=1000441953824; userId=4723660421; userId=4723660421; kuaishou.ad.esp_st=ChJrdWFpc2hvdS5hZC5lc3Auc3QSsAGGviZsywC4h6K90DVqEmbAPTtiTaHw1cmoWfc8g_BKWUgV5F1Mts33fDRcy5zv2triPm9nN6foTwXsGiGfo0wLt-8wkeEeiFGGTeYNubAQPP1YEwPBNK3m124YBSb1xfSRWwCT0j5K_UIN2j54Nx95-7SGnSOX0qBxemeuPJN7ecAhC9-ZmzWWgu8moJOK4ODtYutQGpH4KLDqGqxYogSvnjQZNeTdPr5CNYKzFKgEWBoSSri5zUK8VLCoSWKA3u7_ZSFzIiC1cOVlEWHtpjo3cWNmPR7pkauCmki1zac8tRiZ3Zrr2CgFMAE; kuaishou.ad.esp_ph=b56bc768e61ba93cd963ce4a925925f96d8d; passToken=ChNwYXNzcG9ydC5wYXNzLXRva2VuEsABhJ3VNQBi_x_8G4D55NDY_2JMhuphHw52xKKsVyBp4CdxqAy8oePk71hYyyDZNeCnJh36QGUgJcb_MPB-TJA9oZqTnqNwKxhTxiGisR3LnkI5MvTaxarTq1p9ikGuo0OUGUld_NX3F7YhpXCycyagU3ZLS5wiRQBVPaeS9wlEDUQCut7O5uOJSfmXmIqfX3PFiluJtRdDd9onAgKEOOVkxyt4QUnylAaGD5ci8RIx7MdTLVsgustZNwla1uYSLl_qGhKKuu7N4whAZLzzxMcR5srWdDAiIFd5E0IJA-KheVqeZHOBnqqu9fM1ADAp3MOv6fD6P-_GKAUwAQ; kuaishou.ad.uc_st=ChFrdWFpc2hvdS5hZC51Yy5zdBKwAWmumBdB4PcsBKWFjEe9nDc9bQyxPjJyQ0Qx9tP40UGSsTeBj3fzQ8KJei7-MbBszFMEG8nC__131BodW2NJm5xbvIl-TVyLOuqxviyuYIybNAqNJZmxgWIGa13CU8Qg-6eBuUgNw7C_oZsQO-S0-rCa2araLVMiemQ0KXWP-MRehNfcDrEnvV8492GFUbxlV-j-EVjYHw5KcduFBJmKz4H9NB82kjWgnMuDLjzEgLtYGhJZ7u1ARJXB2V41IEP6K24eQs0iIG0qSSOwwpuaANwnSDJSeOnUlPiOoXwbLg5hk80MCweDKAUwAQ; kuaishou.ad.uc_ph=f704cfecd80ee3f9afa3aacf7c4d3ec27b70
""".strip()

url = "https://niu.e.kuaishou.com/rest/esp/owner/info"
headers = {
    "Cookie": cookies,
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

try:
    resp = requests.post(url, headers=headers)
    print(f"响应状态码: {resp.status_code}")
    print(f"响应头: {resp.headers}")
    print(f"响应内容: {resp.text[:1000]}")
except Exception as e:
    print(f"请求出错: {e}") 