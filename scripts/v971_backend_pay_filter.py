#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v971_backend_pay_filter.py <project_dir>')

root = Path(sys.argv[1])
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# Step 3: send the user's hourly minimum to the backend so the provider search can
# widen specifically for qualifying salary results before the finite response is
# locally filtered. The client still applies its existing filter as a final guard.
old_request = '''            .append("&radius=").append(maxDistanceMiles)
            .append("&source=").append(URLEncoder.encode(backendSourceParam(),"UTF-8"));
        String categoryQuery=backendCategoryQuery();
'''
new_request = '''            .append("&radius=").append(maxDistanceMiles)
            .append("&source=").append(URLEncoder.encode(backendSourceParam(),"UTF-8"));
        url.append("&min_pay_hourly=").append(minPay);
        String categoryQuery=backendCategoryQuery();
'''
if old_request in s:
    s = s.replace(old_request, new_request, 1)
elif 'url.append("&min_pay_hourly=").append(minPay);' not in s:
    raise SystemExit('backend pay query insertion target not found')

# USAJOBS can return daily remuneration. The UI filter is explicitly hourly, so
# convert an 8-hour workday to hourly just as annual/monthly/weekly rates are
# already normalized. Unknown salary remains zero and therefore remains visible.
old_day = '''else if(pay>0&&period.equalsIgnoreCase("week"))pay=pay*52.0/2080.0;String title='''
new_day = '''else if(pay>0&&period.equalsIgnoreCase("week"))pay=pay*52.0/2080.0;else if(pay>0&&period.equalsIgnoreCase("day"))pay=pay/8.0;String title='''
if old_day in s:
    s = s.replace(old_day, new_day, 1)
elif 'period.equalsIgnoreCase("day"))pay=pay/8.0' not in s:
    raise SystemExit('daily salary conversion target not found')

required = [
    'url.append("&min_pay_hourly=").append(minPay);',
    'period.equalsIgnoreCase("day"))pay=pay/8.0',
    '(j.pay<=0||j.pay>=minPay)',
]
for token in required:
    if token not in s:
        raise SystemExit(f'missing Step 3 app token: {token}')

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.71\n', encoding='utf-8')
print('Applied JobBubble V9.4.71 backend-assisted minimum-pay filtering')
