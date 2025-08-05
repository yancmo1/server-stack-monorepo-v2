# COC Database - Detailed Data Analysis
**Companion to Main Analysis Report**

## Player Activity Analysis

### Bonus Distribution Timeline

**March 2025 Mass Bonus Event (25 players):**
```
U Turn, RMax, Amber, noslos, Zeponomous, Klee, LtCol Dad, dad, natey, 
GuchiDconqueror, Death, dnp, jcollind, Souls-On-Fire, knightress, 
anarchy125, /tps, Yancmo, Mini Me, Paddington bear, Tony, MikeyG, 
moose40, ronnie, shz06
```

**January 2025 Bonus Event (5 players):**
```
MachZero, Mason, cocmaster, Ivan Drago, jo
```

**July 2025 Recent Bonus Event (6 players):**
```
wes, Rajan, Ray, J3N, Pirate, Mama Squirrel
```

### CWL Stars Distribution (Current Season)

**Top Performers (20+ stars):**
- Paddington bear: 29 stars
- wes: 26 stars  
- jcollind: 26 stars
- U Turn: 26 stars
- MachZero: 25 stars
- Mason: 25 stars
- dad: 24 stars
- RMax: 24 stars

**Mid-Range Performers (15-19 stars):**
- cocmaster: 22 stars
- Yancmo: 22 stars
- /tps: 22 stars
- Amber: 22 stars
- LtCol Dad: 21 stars
- anarchy125: 20 stars
- Souls-On-Fire: 20 stars
- Rajan: 20 stars
- noslos: 20 stars

**Lower Performers (0-14 stars):**
- MANIA: 18 stars (Leader)
- dnp: 18 stars
- MikeyG: 18 stars
- ronnie: 18 stars
- knightress: 18 stars
- natey: 16 stars
- Death: 16 stars
- jo: 16 stars
- Pirate: 14 stars
- Ivan Drago: 12 stars
- Mama Squirrel: 12 stars
- Mini Me: 12 stars
- moose40: 12 stars
- J3N: 10 stars
- Ray: 6 stars
- shz06: 6 stars
- Klee: 5 stars

**New Members (0 stars):**
- Pokeges: 0 stars (on vacation)
- :-(kridd77)-:: 0 stars
- Cmdr Shepard: 0 stars
- Qbert: 0 stars (inactive)
- GuchiDconqueror: 0 stars (new member)
- Pharaoh: 0 stars (joined July 18)
- Tony: 0 stars (joined July 18)

## Member Tenure Analysis

### Veterans (5+ years)
- **MANIA** (7 years) - Joined March 2018
- **Yancmo** (9 years) - Joined April 2016, Co-Leader
- **Pokeges** (9 years) - Joined April 2016, Co-Leader

### Long-term Members (3-5 years)
- **LtCol Dad** (5 years) - Joined July 2020
- **Zeponomous** (5 years) - Joined July 2020  
- **Death** (4 years) - Joined October 2021
- **Mason** (3 years) - Joined January 2022
- **cocmaster** (3 years) - Joined September 2022

### Recent Additions (2024-2025)
- **Pharaoh** - July 18, 2025 (newest)
- **Tony** - July 18, 2025 (newest)
- **MikeyG** - May 31, 2025
- **Rajan** - April 20, 2025
- **ronnie** - March 8, 2025
- **jcollind** - February 3, 2025

## Geographic Distribution

### Known Locations (5 members):
1. **Moore, OK** - Yancmo (Co-Leader)
2. **Colorado Springs, CO** - Mason (Co-Leader)  
3. **Toronto, ON** - Rajan (Member)
4. **Birmingham, AL** - Death (Elder)
5. **Chicopee, MA** - U Turn (Co-Leader)

### Coverage Analysis:
- **US States Represented:** Oklahoma, Colorado, Alabama, Massachusetts
- **International:** Canada (Toronto)
- **Unknown Locations:** 30 members (85.7%)

## Role Distribution

| Role | Count | Percentage | Notes |
|------|-------|------------|-------|
| Leader | 1 | 2.9% | MANIA |
| Co-Leader | 8 | 22.9% | High leadership ratio |
| Elder | 21 | 60.0% | Majority of clan |
| Member | 5 | 14.3% | New additions |

## Database Technical Details

### Table Sizes and Constraints:
- **Primary Keys:** All tables properly configured
- **Foreign Keys:** CWL tables reference players(name)
- **Indexes:** 20 indexes for performance optimization
- **Sequences:** All auto-increment fields properly configured

### Data Integrity Checks:
✅ All player names unique  
✅ All player tags unique (where provided)  
✅ Bonus history references valid time periods  
✅ No orphaned records found  
✅ Sequence values consistent with data  

### Performance Optimization:
- Indexes on player names, tags, dates
- Proper data types used throughout
- Foreign key constraints maintain referential integrity

## Missing Data Opportunities

### Critical Missing Data:
1. **Player Tags in Bonus History:** 6 recent bonus records missing player tags
2. **War Attack History:** Zero records (major gap for performance analysis)
3. **CWL Historical Data:** No season-over-season tracking
4. **Discord Account Links:** No Discord-COC connections recorded

### Enhancement Opportunities:
1. **Location Collection:** 85% of members missing location data
2. **Favorite Troop Data:** Only Yancmo has this recorded
3. **War Performance Tracking:** Could provide valuable insights
4. **Attack Pattern Analysis:** Currently not captured

## Recommendations Priority Matrix

### High Priority (Immediate):
1. ✅ Collect missing player tags for bonus history
2. ✅ Enable war attack logging
3. ✅ Implement regular database backups

### Medium Priority (Next Month):
1. 🔧 Discord account linking campaign
2. 🔧 Location data collection for map functionality
3. 🔧 CWL historical performance tracking

### Low Priority (Future Enhancement):
1. 📈 Advanced analytics and reporting
2. 📈 Attack pattern analysis
3. 📈 Performance prediction models

---

*Detailed analysis of 35 active clan members across 9 database tables*  
*Total database size: ~25KB with significant growth potential*
