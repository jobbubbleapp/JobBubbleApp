#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v975_unit_testable_job_logic.py <project_dir>')

root = Path(sys.argv[1]).resolve()
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
logic = root / 'app/src/main/java/com/jobbubble/app/JobLogic.java'
test = root / 'app/src/test/java/com/jobbubble/app/JobLogicTest.java'
gradle = root / 'app/build.gradle'
version = root / 'VERSION.txt'

s = main.read_text(encoding='utf-8')

def replace_method(text, name, replacement):
    pattern = re.compile(r'(?ms)^    private String ' + re.escape(name) + r'\(\)\{.*?^    \}\n')
    found = pattern.search(text)
    if not found:
        raise SystemExit(f'could not find {name} method')
    return text[:found.start()] + replacement + text[found.end():]

s = replace_method(s, 'backendCategoryQuery', '    private String backendCategoryQuery(){return JobLogic.backendCategoryQuery(category);}\n')
s = replace_method(s, 'backendSourceParam', '    private String backendSourceParam(){return JobLogic.backendSourceParam(source);}\n')

old_distance = '    private String money(double x){return String.format(Locale.US,"%.1f",x);} private double distanceMiles(double a,double b,double c,double d){double R=3958.761,p=Math.toRadians(c-a),q=Math.toRadians(d-b),x=Math.sin(p/2)*Math.sin(p/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(q/2)*Math.sin(q/2);return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}'
new_distance = '    private String money(double x){return String.format(Locale.US,"%.1f",x);} private double distanceMiles(double a,double b,double c,double d){return JobLogic.distanceMiles(a,b,c,d);}'
if old_distance not in s:
    raise SystemExit('distanceMiles production target not found')
s = s.replace(old_distance, new_distance, 1)

old_pay = 'double pay=o.optDouble("salary_min",0);String period=o.optString("salary_period","");if(pay>0&&period.equalsIgnoreCase("year"))pay=pay/2080.0;else if(pay>0&&period.equalsIgnoreCase("month"))pay=pay*12.0/2080.0;else if(pay>0&&period.equalsIgnoreCase("week"))pay=pay*52.0/2080.0;else if(pay>0&&period.equalsIgnoreCase("day"))pay=pay/8.0;String title='
new_pay = 'double pay=JobLogic.hourlyPay(o.optDouble("salary_min",0),o.optString("salary_period",""));String title='
if old_pay not in s:
    raise SystemExit('Job.from salary conversion target not found')
s = s.replace(old_pay, new_pay, 1)
main.write_text(s, encoding='utf-8')

logic.parent.mkdir(parents=True, exist_ok=True)
logic.write_text('''package com.jobbubble.app;\n\nfinal class JobLogic {\n    private JobLogic() {}\n\n    static String backendCategoryQuery(String category) {\n        if (category == null) return "";\n        switch (category) {\n            case "Retail & Sales": return "retail";\n            case "Warehouse & Logistics": return "warehouse";\n            case "Food & Hospitality": return "restaurant";\n            case "Construction & Skilled Trades": return "construction";\n            case "Office & Administration": return "administrative";\n            case "Customer Service": return "customer service";\n            case "Healthcare": return "healthcare";\n            case "Transportation & Delivery": return "driver";\n            case "Security & Public Safety": return "security";\n            case "Technology & Engineering": return "technology";\n            case "Government": return "government";\n            case "Education": return "education";\n            case "Finance & Accounting": return "accounting";\n            case "Manufacturing": return "manufacturing";\n            case "Cleaning & Facilities": return "janitorial";\n            default: return "";\n        }\n    }\n\n    static String backendSourceParam(String source) {\n        if ("Adzuna".equalsIgnoreCase(source)) return "adzuna";\n        if ("USAJOBS".equalsIgnoreCase(source)) return "usajobs";\n        if ("The Muse".equalsIgnoreCase(source)) return "themuse";\n        return "all";\n    }\n\n    static double hourlyPay(double pay, String period) {\n        if (!(pay > 0)) return pay;\n        String p = period == null ? "" : period;\n        if (p.equalsIgnoreCase("year")) return pay / 2080.0;\n        if (p.equalsIgnoreCase("month")) return pay * 12.0 / 2080.0;\n        if (p.equalsIgnoreCase("week")) return pay * 52.0 / 2080.0;\n        if (p.equalsIgnoreCase("day")) return pay / 8.0;\n        return pay;\n    }\n\n    static double distanceMiles(double lat1, double lon1, double lat2, double lon2) {\n        double radius = 3958.761;\n        double p = Math.toRadians(lat2 - lat1);\n        double q = Math.toRadians(lon2 - lon1);\n        double x = Math.sin(p / 2) * Math.sin(p / 2)\n            + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))\n            * Math.sin(q / 2) * Math.sin(q / 2);\n        return radius * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));\n    }\n}\n''', encoding='utf-8')

test.parent.mkdir(parents=True, exist_ok=True)
test.write_text('''package com.jobbubble.app;\n\nimport static org.junit.Assert.*;\nimport org.junit.Test;\n\npublic class JobLogicTest {\n    @Test public void categoryMappingsStayStable() {\n        assertEquals("retail", JobLogic.backendCategoryQuery("Retail & Sales"));\n        assertEquals("warehouse", JobLogic.backendCategoryQuery("Warehouse & Logistics"));\n        assertEquals("restaurant", JobLogic.backendCategoryQuery("Food & Hospitality"));\n        assertEquals("customer service", JobLogic.backendCategoryQuery("Customer Service"));\n        assertEquals("", JobLogic.backendCategoryQuery("All jobs"));\n        assertEquals("", JobLogic.backendCategoryQuery(null));\n    }\n\n    @Test public void sourceMappingsStayStable() {\n        assertEquals("adzuna", JobLogic.backendSourceParam("Adzuna"));\n        assertEquals("usajobs", JobLogic.backendSourceParam("USAJOBS"));\n        assertEquals("themuse", JobLogic.backendSourceParam("The Muse"));\n        assertEquals("all", JobLogic.backendSourceParam("All sources"));\n        assertEquals("all", JobLogic.backendSourceParam(null));\n    }\n\n    @Test public void salaryPeriodsNormalizeToHourly() {\n        assertEquals(25.0, JobLogic.hourlyPay(52000, "year"), 0.0001);\n        assertEquals(30.0, JobLogic.hourlyPay(5200, "month"), 0.0001);\n        assertEquals(25.0, JobLogic.hourlyPay(1000, "week"), 0.0001);\n        assertEquals(25.0, JobLogic.hourlyPay(200, "day"), 0.0001);\n        assertEquals(25.0, JobLogic.hourlyPay(25, "hour"), 0.0001);\n        assertEquals(0.0, JobLogic.hourlyPay(0, "year"), 0.0001);\n    }\n\n    @Test public void distanceUsesMilesAndIsSymmetric() {\n        assertEquals(0.0, JobLogic.distanceMiles(47.6062, -122.3321, 47.6062, -122.3321), 0.000001);\n        double seattleEverett = JobLogic.distanceMiles(47.6062, -122.3321, 47.9790, -122.2021);\n        assertTrue(seattleEverett > 25.0 && seattleEverett < 35.0);\n        assertEquals(seattleEverett, JobLogic.distanceMiles(47.9790, -122.2021, 47.6062, -122.3321), 0.000001);\n    }\n}\n''', encoding='utf-8')

g = gradle.read_text(encoding='utf-8')
if "testImplementation 'junit:junit:4.13.2'" not in g:
    marker = "    implementation 'com.google.firebase:firebase-firestore:25.1.4'\n"
    if marker not in g:
        raise SystemExit('Gradle dependency insertion point not found')
    g = g.replace(marker, marker + "    testImplementation 'junit:junit:4.13.2'\n", 1)

if not re.search(r'(?m)^\s*targetSdk\s+35\s*$', g):
    raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g = re.sub(r'(?m)^\s*versionCode\s+81\s*$', '        versionCode 82', g, count=1)
g = re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.74['\"]\s*$", "        versionName '9.4.75'", g, count=1)
gradle.write_text(g, encoding='utf-8')
version.write_text('9.4.75\n', encoding='utf-8')

final = main.read_text(encoding='utf-8')
for token in [
    'JobLogic.backendCategoryQuery(category)',
    'JobLogic.backendSourceParam(source)',
    'JobLogic.distanceMiles(a,b,c,d)',
    'JobLogic.hourlyPay(o.optDouble("salary_min",0),o.optString("salary_period",""))'
]:
    if token not in final:
        raise SystemExit(f'missing Step 9 production delegation: {token}')
print('Applied JobBubble V9.4.75 unit-testable job logic with JUnit regression tests')
