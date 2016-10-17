from urlparse import parse_qs, urlparse

VERSION = 'v0.3.1'

def stats(resp):
    if resp.history:
        print("\n\033[94mHistory\033[0m")
        for redirect in resp.history:
            print("{}: {}".format(redirect.url, redirect.status_code))


    print("\n\033[94mGeneral\033[0m")
    print("Request URL: {}".format(resp.url))
    print("Request Method: {}".format(resp.request.method))
    print("Status Code: {}".format(resp.status_code))


    print("\n\033[94mResponse Headers\033[0m")
    for k, v in sorted(resp.headers.items(), key=lambda s: s[0].lower()):
        print("{}: {}".format(k, v))


    print("\n\033[94mRequest Headers\033[0m")
    for k, v in sorted(resp.request.headers.items(), key=lambda s: s[0].lower()):
        print("{}: {}".format(k, v))


    qs_params = parse_qs(urlparse(resp.url).query)
    if qs_params:
        print("\n\033[94mQuery String Parms\033[0m")
        for k, v in sorted(qs_params.items()):
            print("{}: {}".format(k, ', '.join(v)))

    print


H_COMMON = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
        }

H_AJAX = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        }


H_FORM = H_COMMON.copy()
H_FORM.update({
        "Content-Type": "application/x-www-form-urlencoded",
        })
