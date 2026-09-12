#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v952_muse_location_query_fix.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# The Muse backend search is sensitive to the textual location. Android reverse
# geocoding returns full state names (for example "Everett, Washington"), while
# the provider returns the correct local result set for the standard city/state
# form ("Everett, WA"). Keep the display label untouched and normalize only the
# value sent to the job backend.
helper = '''    private String usStateAbbreviation(String state){
        if(state==null)return "";
        String value=state.trim();
        if(value.matches("(?i)^[A-Z]{2}$"))return value.toUpperCase(Locale.US);
        switch(value.toLowerCase(Locale.US)){
            case "alabama":return "AL";
            case "alaska":return "AK";
            case "arizona":return "AZ";
            case "arkansas":return "AR";
            case "california":return "CA";
            case "colorado":return "CO";
            case "connecticut":return "CT";
            case "delaware":return "DE";
            case "district of columbia":case "washington dc":case "washington d.c.":return "DC";
            case "florida":return "FL";
            case "georgia":return "GA";
            case "hawaii":return "HI";
            case "idaho":return "ID";
            case "illinois":return "IL";
            case "indiana":return "IN";
            case "iowa":return "IA";
            case "kansas":return "KS";
            case "kentucky":return "KY";
            case "louisiana":return "LA";
            case "maine":return "ME";
            case "maryland":return "MD";
            case "massachusetts":return "MA";
            case "michigan":return "MI";
            case "minnesota":return "MN";
            case "mississippi":return "MS";
            case "missouri":return "MO";
            case "montana":return "MT";
            case "nebraska":return "NE";
            case "nevada":return "NV";
            case "new hampshire":return "NH";
            case "new jersey":return "NJ";
            case "new mexico":return "NM";
            case "new york":return "NY";
            case "north carolina":return "NC";
            case "north dakota":return "ND";
            case "ohio":return "OH";
            case "oklahoma":return "OK";
            case "oregon":return "OR";
            case "pennsylvania":return "PA";
            case "rhode island":return "RI";
            case "south carolina":return "SC";
            case "south dakota":return "SD";
            case "tennessee":return "TN";
            case "texas":return "TX";
            case "utah":return "UT";
            case "vermont":return "VT";
            case "virginia":return "VA";
            case "washington":return "WA";
            case "west virginia":return "WV";
            case "wisconsin":return "WI";
            case "wyoming":return "WY";
            case "puerto rico":return "PR";
            case "guam":return "GU";
            case "u.s. virgin islands":case "us virgin islands":case "virgin islands":return "VI";
            case "american samoa":return "AS";
            case "northern mariana islands":case "commonwealth of the northern mariana islands":return "MP";
            default:return value;
        }
    }

    private String normalizeBackendWhere(String where){
        if(where==null)return "";
        String value=where.trim();
        int comma=value.lastIndexOf(',');
        if(comma<0)return value;
        String place=value.substring(0,comma).trim();
        String region=value.substring(comma+1).trim();
        String normalizedRegion=usStateAbbreviation(region);
        if(place.isEmpty()||normalizedRegion.isEmpty())return value;
        return place+", "+normalizedRegion;
    }

'''

marker = '    private String buildJobRequestUrl(String endpoint,String where,String savedWhere,boolean refined)throws Exception{\n'
if 'private String normalizeBackendWhere(String where)' not in s:
    if marker not in s:
        raise SystemExit('buildJobRequestUrl marker not found')
    s = s.replace(marker, helper + marker, 1)

old = '            .append("?where=").append(URLEncoder.encode(where,"UTF-8"))\n'
new = '            .append("?where=").append(URLEncoder.encode(normalizeBackendWhere(where),"UTF-8"))\n'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('where URL encoding target not found')

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.52\n', encoding='utf-8')
print('Applied JobBubble V9.4.52 Muse city/state query normalization')
