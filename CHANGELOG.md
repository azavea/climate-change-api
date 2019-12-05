# Change Log

## [2.8.0](https://github.com/azavea/climate-change-api/tree/2.8.0) (2019-12-05)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.7.1...2.8.0)

**Merged pull requests:**

- Post user signups to HubSpot instead of Salesforce [\#889](https://github.com/azavea/climate-change-api/pull/889)
- Revert most port changes for application [\#887](https://github.com/azavea/climate-change-api/pull/887)
- Remap ports to avoid conflicts with DistrictBuilder [\#886](https://github.com/azavea/climate-change-api/pull/886)

## [2.7.1](https://github.com/azavea/climate-change-api/tree/2.7.1) (2019-05-08)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.6.0...2.7.1)

**Merged pull requests:**

- Feature/mvm/django 1 11 [\#884](https://github.com/azavea/climate-change-api/pull/884)
- Upgrade to Django 1.11 and Python 3.6 [\#882](https://github.com/azavea/climate-change-api/pull/882)
- Don't require city id in project json schema [\#875](https://github.com/azavea/climate-change-api/pull/875)
- Bump dependency versions for docker-compose [\#842](https://github.com/azavea/climate-change-api/pull/842)

## [2.6.0](https://github.com/azavea/climate-change-api/tree/2.6.0) (2019-01-16)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.5.0...2.6.0)

**Merged pull requests:**

- Correct /api/map-cell/ endpoint to return 404 when no data is found [\#873](https://github.com/azavea/climate-change-api/pull/873)
- Fix bugs in the climate data lat/lon endpoints [\#871](https://github.com/azavea/climate-change-api/pull/871)
- Update climate data import documentation [\#868](https://github.com/azavea/climate-change-api/pull/868)
- Merge 'lat-lon-map-cell-distance-list' view into 'lat-lon-map-cell-list' [\#866](https://github.com/azavea/climate-change-api/pull/866)
- Return valid 4326 longitudes in map-cell endpoints [\#864](https://github.com/azavea/climate-change-api/pull/864)
- Feature/kak/query by distance\#855 [\#856](https://github.com/azavea/climate-change-api/pull/856)
- Revert "Temporarily remove docs for new by lat/lon endpoints" [\#853](https://github.com/azavea/climate-change-api/pull/853)

## [2.5.0](https://github.com/azavea/climate-change-api/tree/2.5.0) (2018-12-11)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.4.1...2.5.0)

**Merged pull requests:**

- Add additional location sources  [\#854](https://github.com/azavea/climate-change-api/pull/854)
- Temporarily remove docs for new by lat/lon endpoints [\#852](https://github.com/azavea/climate-change-api/pull/852)
- Fix crash due to type mismatch in percentile indicators [\#851](https://github.com/azavea/climate-change-api/pull/851)
- Supply dataset context for ClimateDataCellSerializer [\#850](https://github.com/azavea/climate-change-api/pull/850)
- Add API endpoint to get map cells for a lat/lon point [\#849](https://github.com/azavea/climate-change-api/pull/849)
- Update Lat + Lon API views with ocean proximity [\#846](https://github.com/azavea/climate-change-api/pull/846)
- Add ClimateDataCell.is\_coastal field and populate via Coastline [\#845](https://github.com/azavea/climate-change-api/pull/845)
- Add API view to query climate data  by Lat + Lon [\#843](https://github.com/azavea/climate-change-api/pull/843)
- Refactor Nex2DB to allow importing cells based on a MultiPolygon shapefile [\#841](https://github.com/azavea/climate-change-api/pull/841)

## [2.4.1](https://github.com/azavea/climate-change-api/tree/2.4.1) (2018-08-20)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.4.0...2.4.1)

**Merged pull requests:**

- Use static template tag for Temperate logo [\#835](https://github.com/azavea/climate-change-api/pull/835)

## [2.4.0](https://github.com/azavea/climate-change-api/tree/2.4.0) (2018-08-20)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.3.0...2.4.0)

**Merged pull requests:**

- Add temperate ad text below login block [\#833](https://github.com/azavea/climate-change-api/pull/833)

## [2.3.0](https://github.com/azavea/climate-change-api/tree/2.3.0) (2018-07-06)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.2.2...2.3.0)

**Merged pull requests:**

- Fix City detail page on Django Admin [\#828](https://github.com/azavea/climate-change-api/pull/828)
- Pull SSL certificate ARN from remote state [\#827](https://github.com/azavea/climate-change-api/pull/827)
- Move dynamic checking of which datasets a City supports to a DB field [\#825](https://github.com/azavea/climate-change-api/pull/825)

## [2.2.2](https://github.com/azavea/climate-change-api/tree/2.2.2) (2018-07-02)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.2.1...2.2.2)

**Merged pull requests:**

- Add documentation for the single city ingest process [\#814](https://github.com/azavea/climate-change-api/pull/814)
- Add alias to scenario definition for user projects [\#811](https://github.com/azavea/climate-change-api/pull/811)
- Feature/jf/deployment docs update [\#808](https://github.com/azavea/climate-change-api/pull/808)

## [2.2.1](https://github.com/azavea/climate-change-api/tree/2.2.1) (2018-04-18)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.2.0...2.2.1)

**Merged pull requests:**

- Allow processing only cities missing data for source during import [\#804](https://github.com/azavea/climate-change-api/pull/804)

## [2.2.0](https://github.com/azavea/climate-change-api/tree/2.2.0) (2018-03-12)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.6...2.2.0)

**Merged pull requests:**

- Add alias field to scenario [\#797](https://github.com/azavea/climate-change-api/pull/797)

## [2.1.6](https://github.com/azavea/climate-change-api/tree/2.1.6) (2018-01-31)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.5...2.1.6)

**Merged pull requests:**

- Update city cell during import [\#795](https://github.com/azavea/climate-change-api/pull/795)
- Add geonames city importer [\#793](https://github.com/azavea/climate-change-api/pull/793)

## [2.1.5](https://github.com/azavea/climate-change-api/tree/2.1.5) (2018-01-29)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.4...2.1.5)

**Merged pull requests:**

- Update django registration [\#794](https://github.com/azavea/climate-change-api/pull/794)
- Allow managing user throttling rates in Admin panel [\#790](https://github.com/azavea/climate-change-api/pull/790)

## [2.1.4](https://github.com/azavea/climate-change-api/tree/2.1.4) (2017-12-11)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.3...2.1.4)

**Merged pull requests:**

- Move is\_coastal into a proximity grouping [\#788](https://github.com/azavea/climate-change-api/pull/788)
- Style password reset page [\#786](https://github.com/azavea/climate-change-api/pull/786)
- Add management command to update cities [\#777](https://github.com/azavea/climate-change-api/pull/777)
- Fixup is\_coastal changes [\#775](https://github.com/azavea/climate-change-api/pull/775)
- Support incremental nex2db inserts for new cities [\#774](https://github.com/azavea/climate-change-api/pull/774)

## [2.1.3](https://github.com/azavea/climate-change-api/tree/2.1.3) (2017-11-20)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.2...2.1.3)

**Merged pull requests:**

- Allow requesting API token of current user for any origin in non-prod envs [\#767](https://github.com/azavea/climate-change-api/pull/767)
- Feature/kak/coastal\#753 [\#764](https://github.com/azavea/climate-change-api/pull/764)
- Feature/kak/updates\#725 [\#761](https://github.com/azavea/climate-change-api/pull/761)

## [2.1.2](https://github.com/azavea/climate-change-api/tree/2.1.2) (2017-11-15)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.1...2.1.2)

**Merged pull requests:**

- Historic baseline by dataset [\#756](https://github.com/azavea/climate-change-api/pull/756)

## [2.1.1](https://github.com/azavea/climate-change-api/tree/2.1.1) (2017-11-14)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.1.0...2.1.1)

**Merged pull requests:**

- Add a new endpoint for the Lab to request the token of the logged in user [\#755](https://github.com/azavea/climate-change-api/pull/755)
- Copy data to ram to speed up nex2db [\#754](https://github.com/azavea/climate-change-api/pull/754)
- Add ADR-0009: Use AWS Batch for single city ingest [\#745](https://github.com/azavea/climate-change-api/pull/745)
- Remove duplicate field [\#744](https://github.com/azavea/climate-change-api/pull/744)
- Add refresh token API endpoint [\#736](https://github.com/azavea/climate-change-api/pull/736)

## [2.1.0](https://github.com/azavea/climate-change-api/tree/2.1.0) (2017-10-17)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/2.0.0...2.1.0)

**Merged pull requests:**

- Redirect to application home on login [\#738](https://github.com/azavea/climate-change-api/pull/738)
- Clarify ClimateUser creation documentation [\#735](https://github.com/azavea/climate-change-api/pull/735)
- Update copy [\#733](https://github.com/azavea/climate-change-api/pull/733)
- Style changes and HTML changes made, just waiting on content. Also ad… [\#731](https://github.com/azavea/climate-change-api/pull/731)
- Style changes and HTML changes made, just waiting on content. Also ad… [\#730](https://github.com/azavea/climate-change-api/pull/730)
- Set Lab/Docs links based on settings.ENVIRONMENT [\#727](https://github.com/azavea/climate-change-api/pull/727)
- Update header for lab integration [\#724](https://github.com/azavea/climate-change-api/pull/724)
- Scaffold the "app page", "account profile" and "api page" [\#722](https://github.com/azavea/climate-change-api/pull/722)
- Update instructions for dumping staging database in README.rst [\#716](https://github.com/azavea/climate-change-api/pull/716)
- Update relevant indicators to use precipitation rates [\#711](https://github.com/azavea/climate-change-api/pull/711)
- Fix City Map Cell and incomplete ClimateDataSource datachecks [\#709](https://github.com/azavea/climate-change-api/pull/709)
- Replace internal static-site with terraform-aws-s3-origin [\#708](https://github.com/azavea/climate-change-api/pull/708)
- Use project specific RDS database name [\#705](https://github.com/azavea/climate-change-api/pull/705)
- Use project specific Papertrail settings [\#703](https://github.com/azavea/climate-change-api/pull/703)
- Feature/kak/update project schema dataset\#700 [\#701](https://github.com/azavea/climate-change-api/pull/701)
- Update project schema with datasets property [\#693](https://github.com/azavea/climate-change-api/pull/693)
- Feature/kak/model dataset combo check\#665 [\#692](https://github.com/azavea/climate-change-api/pull/692)
- Connect API infrastructure with core infrastructure [\#691](https://github.com/azavea/climate-change-api/pull/691)
- Allow importing LOCA data from remote instances [\#690](https://github.com/azavea/climate-change-api/pull/690)
- Add lab librato tag [\#677](https://github.com/azavea/climate-change-api/pull/677)

## [2.0.0](https://github.com/azavea/climate-change-api/tree/2.0.0) (2017-09-18)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.2.1...2.0.0)

**Merged pull requests:**

- Add dataset name to climate data/indicator response [\#687](https://github.com/azavea/climate-change-api/pull/687)
- Document dry spells [\#686](https://github.com/azavea/climate-change-api/pull/686)
- Mark yearly dry spells indicator as deprecated [\#684](https://github.com/azavea/climate-change-api/pull/684)
- Feature/kak/fix docs search titles\#658 [\#683](https://github.com/azavea/climate-change-api/pull/683)
- Immediately realize map generators in create\_jobs.py [\#680](https://github.com/azavea/climate-change-api/pull/680)
- Fix issues with LOCA staging import via run\_jobs.py [\#679](https://github.com/azavea/climate-change-api/pull/679)
- Add ClimateDataset API documentation [\#675](https://github.com/azavea/climate-change-api/pull/675)
- API view updates for ClimateDataset \<--\> ClimateModel ManyToMany relationship [\#674](https://github.com/azavea/climate-change-api/pull/674)
- Associate ClimateModel objects with appropriate ClimateDataset [\#670](https://github.com/azavea/climate-change-api/pull/670)
- Add ClimateDataCityCellSerializer and city map\_cell detail view [\#669](https://github.com/azavea/climate-change-api/pull/669)
- Feature/csh/add deserialize to indicatorparams [\#660](https://github.com/azavea/climate-change-api/pull/660)
- Add LOCA data to relevant API views [\#652](https://github.com/azavea/climate-change-api/pull/652)

## [1.2.1](https://github.com/azavea/climate-change-api/tree/1.2.1) (2017-09-07)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.2.0...1.2.1)

**Merged pull requests:**

- Feature/awf/fix latest django migrations [\#657](https://github.com/azavea/climate-change-api/pull/657)
- Livin la vida LOCA [\#653](https://github.com/azavea/climate-change-api/pull/653)
- Add extra params field to project schema [\#649](https://github.com/azavea/climate-change-api/pull/649)
- Add ClimateDataset model and make City\<-\>Cell many-to-many [\#644](https://github.com/azavea/climate-change-api/pull/644)

## [1.2.0](https://github.com/azavea/climate-change-api/tree/1.2.0) (2017-08-29)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.1.0...1.2.0)

**Merged pull requests:**

- Convert generate\_historic to array data [\#646](https://github.com/azavea/climate-change-api/pull/646)
- Send user's name as librato tag [\#645](https://github.com/azavea/climate-change-api/pull/645)
- Remove ClimateData model [\#639](https://github.com/azavea/climate-change-api/pull/639)
- ADR 0008: Repository Split for ICLEI app [\#635](https://github.com/azavea/climate-change-api/pull/635)
- Change import\_from\_other\_instance to use ClimateDataYear [\#631](https://github.com/azavea/climate-change-api/pull/631)
- Migrate run\_jobs.py to use ClimateDataYear [\#610](https://github.com/azavea/climate-change-api/pull/610)

## [1.1.0](https://github.com/azavea/climate-change-api/tree/1.1.0) (2017-08-16)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.9...1.1.0)

**Merged pull requests:**

- Correct some commands in README.rst for producing db dumps [\#632](https://github.com/azavea/climate-change-api/pull/632)
- Upgrade development environment to Docker 17 [\#625](https://github.com/azavea/climate-change-api/pull/625)
- Remove deprecated setting [\#613](https://github.com/azavea/climate-change-api/pull/613)
- Add unit to chart project schema [\#608](https://github.com/azavea/climate-change-api/pull/608)
- Iterative ClimateDataYear migration [\#607](https://github.com/azavea/climate-change-api/pull/607)
- Remove requirement for multiChartScrubber in user projects [\#606](https://github.com/azavea/climate-change-api/pull/606)
- Feature/awf/integrate custom time partitioner validator [\#604](https://github.com/azavea/climate-change-api/pull/604)
- Array historic data and heatwave indicators [\#602](https://github.com/azavea/climate-change-api/pull/602)
- Add CustomTimeParamValidator and use for appropriate API param [\#598](https://github.com/azavea/climate-change-api/pull/598)
- Add support for extreme meteorological event indicators [\#597](https://github.com/azavea/climate-change-api/pull/597)
- Implement Accumulated Freezing Degree Days using Array Data [\#595](https://github.com/azavea/climate-change-api/pull/595)
- Convert frost days to array indicator [\#592](https://github.com/azavea/climate-change-api/pull/592)
- Add array data support for percentile indicators [\#591](https://github.com/azavea/climate-change-api/pull/591)
- Remove time specification from year-specific indicator names [\#590](https://github.com/azavea/climate-change-api/pull/590)
- Convert total precip indicator to array indicator [\#585](https://github.com/azavea/climate-change-api/pull/585)
- Add ArrayIndicator version of YearlyMaxConsecutiveDryDays [\#584](https://github.com/azavea/climate-change-api/pull/584)
- Custom time aggregation for array indicators [\#583](https://github.com/azavea/climate-change-api/pull/583)
- Add StatsD companion container to management task definition [\#582](https://github.com/azavea/climate-change-api/pull/582)
- Add cooling and heating degree days support for array data [\#580](https://github.com/azavea/climate-change-api/pull/580)
- Feature/jf/new threshold indicators [\#579](https://github.com/azavea/climate-change-api/pull/579)
- Add diurnal temperature range support for array data [\#576](https://github.com/azavea/climate-change-api/pull/576)
- Feature/kak/raw climate data yearly\#537 [\#575](https://github.com/azavea/climate-change-api/pull/575)
- Fix misnamed terraform variable assignment [\#573](https://github.com/azavea/climate-change-api/pull/573)
- Add offset yearly time aggregation [\#557](https://github.com/azavea/climate-change-api/pull/557)

## [1.0.9](https://github.com/azavea/climate-change-api/tree/1.0.9) (2017-07-18)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.8...1.0.9)

**Merged pull requests:**

- Fix copy-and-paste error [\#569](https://github.com/azavea/climate-change-api/pull/569)
- Set CC\_FF\_ARRAY\_DATA in development environments [\#568](https://github.com/azavea/climate-change-api/pull/568)
- Avoid memory issues, batch process generate\_historic.py data in chunks [\#566](https://github.com/azavea/climate-change-api/pull/566)
- Introduce feature flag for ClimateDataYear indicators [\#565](https://github.com/azavea/climate-change-api/pull/565)
- Split ClimateDataYear data migration and schema migration [\#564](https://github.com/azavea/climate-change-api/pull/564)
- Store and process ClimateData by year chunks [\#527](https://github.com/azavea/climate-change-api/pull/527)

## [1.0.8](https://github.com/azavea/climate-change-api/tree/1.0.8) (2017-07-17)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.7...1.0.8)

**Merged pull requests:**

- Send indicator name as tag to Librato [\#563](https://github.com/azavea/climate-change-api/pull/563)
- Librato tagged metrics [\#539](https://github.com/azavea/climate-change-api/pull/539)
- Remove individual foreign key requests for city view [\#538](https://github.com/azavea/climate-change-api/pull/538)
- Add Django Debug Toolbar [\#522](https://github.com/azavea/climate-change-api/pull/522)
- Add historic\_range param to docs [\#519](https://github.com/azavea/climate-change-api/pull/519)
- Feature/jf/custom historical ranges [\#506](https://github.com/azavea/climate-change-api/pull/506)

## [1.0.7](https://github.com/azavea/climate-change-api/tree/1.0.7) (2017-06-26)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.6...1.0.7)

**Merged pull requests:**

- Feature/jf/custom historical ranges tests [\#521](https://github.com/azavea/climate-change-api/pull/521)
- Fixup librato sink to work with new Librato Tags API [\#518](https://github.com/azavea/climate-change-api/pull/518)

## [1.0.6](https://github.com/azavea/climate-change-api/tree/1.0.6) (2017-06-20)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.5...1.0.6)

**Merged pull requests:**

- Add favicons to API and docs [\#514](https://github.com/azavea/climate-change-api/pull/514)
- Add feedback section to profile [\#513](https://github.com/azavea/climate-change-api/pull/513)
- Only send metrics for content length if response.content exists [\#512](https://github.com/azavea/climate-change-api/pull/512)
- Fix docs typo [\#508](https://github.com/azavea/climate-change-api/pull/508)
- Add search filter param to City list [\#501](https://github.com/azavea/climate-change-api/pull/501)
- Fix broken docs search [\#500](https://github.com/azavea/climate-change-api/pull/500)
- Feature/awf/django api requests middleware [\#486](https://github.com/azavea/climate-change-api/pull/486)
- Feature/awf/statsite container [\#485](https://github.com/azavea/climate-change-api/pull/485)
- Add ADR0007: API Request Logging [\#475](https://github.com/azavea/climate-change-api/pull/475)
- Formalize, standardize and document CityList filter options [\#474](https://github.com/azavea/climate-change-api/pull/474)
- Feature/jf/dtr indicator [\#472](https://github.com/azavea/climate-change-api/pull/472)
- Django dependencies upgrade [\#467](https://github.com/azavea/climate-change-api/pull/467)
- Ensure django.conf.settings aren't evaluated until after running command [\#466](https://github.com/azavea/climate-change-api/pull/466)

## [1.0.5](https://github.com/azavea/climate-change-api/tree/1.0.5) (2017-05-19)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.4...1.0.5)

**Merged pull requests:**

- Remove traces of custom BigAutoField [\#471](https://github.com/azavea/climate-change-api/pull/471)
- Bump django extensions version [\#463](https://github.com/azavea/climate-change-api/pull/463)
- Django 1.10 upgrade [\#461](https://github.com/azavea/climate-change-api/pull/461)
- Feature/jdf/style registration form [\#459](https://github.com/azavea/climate-change-api/pull/459)
- Feature/jf/hookup salesforce [\#458](https://github.com/azavea/climate-change-api/pull/458)
- Style registration form [\#457](https://github.com/azavea/climate-change-api/pull/457)
- Open all external links in docs in new tab [\#451](https://github.com/azavea/climate-change-api/pull/451)
- Restore development DB from an S3 backup [\#449](https://github.com/azavea/climate-change-api/pull/449)
- Fix healthchecks to check for scenario data within correct time range [\#446](https://github.com/azavea/climate-change-api/pull/446)
- Update load tests [\#402](https://github.com/azavea/climate-change-api/pull/402)

## [1.0.4](https://github.com/azavea/climate-change-api/tree/1.0.4) (2017-04-26)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.3...1.0.4)

**Merged pull requests:**

- Merge branch 'release/1.0.3' [\#455](https://github.com/azavea/climate-change-api/pull/455)

## [1.0.3](https://github.com/azavea/climate-change-api/tree/1.0.3) (2017-04-26)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.2...1.0.3)

## [1.0.2](https://github.com/azavea/climate-change-api/tree/1.0.2) (2017-04-26)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.1...1.0.2)

**Merged pull requests:**

- Fix broken img reference in logout page [\#453](https://github.com/azavea/climate-change-api/pull/453)
- Update to open registration in all cases [\#452](https://github.com/azavea/climate-change-api/pull/452)
- Fix deployment of static assets [\#450](https://github.com/azavea/climate-change-api/pull/450)
- Install pydocstyle version compatible with flake8-docstrings [\#448](https://github.com/azavea/climate-change-api/pull/448)
- Quote passing of Git commit SHA to Terraform [\#445](https://github.com/azavea/climate-change-api/pull/445)
- Move data health checks to API [\#443](https://github.com/azavea/climate-change-api/pull/443)
- Bump terraform version to 0.9.3 [\#439](https://github.com/azavea/climate-change-api/pull/439)
- Release 1.0.1, update Changelog [\#432](https://github.com/azavea/climate-change-api/pull/432)

## [1.0.1](https://github.com/azavea/climate-change-api/tree/1.0.1) (2017-04-19)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/1.0.0...1.0.1)

## [1.0.0](https://github.com/azavea/climate-change-api/tree/1.0.0) (2017-04-19)

[Full Changelog](https://github.com/azavea/climate-change-api/compare/e487f62fd17c1a974a299f2ee374d8f3353fd893...1.0.0)

**Merged pull requests:**

- Feature/jf/docs copy edit [\#431](https://github.com/azavea/climate-change-api/pull/431)
- Copy edit documentation [\#430](https://github.com/azavea/climate-change-api/pull/430)
- Remove localhost ref in SCSS url for climate logo [\#428](https://github.com/azavea/climate-change-api/pull/428)
- Cleanup work toward a production deployment [\#427](https://github.com/azavea/climate-change-api/pull/427)
- Add volume mount to `management` tasks. [\#426](https://github.com/azavea/climate-change-api/pull/426)
- Require organization for registration [\#424](https://github.com/azavea/climate-change-api/pull/424)
- Remove inconsitent historical year references and clarify Indicators docs copy [\#423](https://github.com/azavea/climate-change-api/pull/423)
- Convert ClimateData to use bigint for id [\#422](https://github.com/azavea/climate-change-api/pull/422)
- Add indicators descriptions 4/4 [\#417](https://github.com/azavea/climate-change-api/pull/417)
- Account pages quality of life improvements [\#409](https://github.com/azavea/climate-change-api/pull/409)
- Disable data health checks [\#406](https://github.com/azavea/climate-change-api/pull/406)
- Feature/kak/fix region import ram\#399 [\#405](https://github.com/azavea/climate-change-api/pull/405)
- Update API title to "Climate API" throughout docs [\#404](https://github.com/azavea/climate-change-api/pull/404)
- Indicator Detailed Descriptions -- Part 3 [\#403](https://github.com/azavea/climate-change-api/pull/403)
- Add data health checks [\#398](https://github.com/azavea/climate-change-api/pull/398)
- Mount API load balancer at app. subdomain [\#397](https://github.com/azavea/climate-change-api/pull/397)
- Feature/jf/docs indicators detail 2 [\#386](https://github.com/azavea/climate-change-api/pull/386)
- CSS and styling [\#382](https://github.com/azavea/climate-change-api/pull/382)
- Add terraform 0.9 support [\#381](https://github.com/azavea/climate-change-api/pull/381)
- Add indicator details to docs, part 1/4 [\#378](https://github.com/azavea/climate-change-api/pull/378)
- Update Climate API project to Python 3 [\#377](https://github.com/azavea/climate-change-api/pull/377)
- Accumulated Freezing Degree Days [\#374](https://github.com/azavea/climate-change-api/pull/374)
- Gate Rollbar initialization when DEBUG mode is enabled [\#371](https://github.com/azavea/climate-change-api/pull/371)
- Update DNS to climate.azavea.com [\#366](https://github.com/azavea/climate-change-api/pull/366)
- \[Addendum\] \#344 SCSS build [\#365](https://github.com/azavea/climate-change-api/pull/365)
- Update DNS references to climate.azavea.com  [\#363](https://github.com/azavea/climate-change-api/pull/363)
- Add SCSS imports example [\#361](https://github.com/azavea/climate-change-api/pull/361)
- Use tagged containers for static asset deployment [\#360](https://github.com/azavea/climate-change-api/pull/360)
- Configure django to take custom SCSS [\#355](https://github.com/azavea/climate-change-api/pull/355)
- Feature/add python linting [\#354](https://github.com/azavea/climate-change-api/pull/354)
- Remove root API view from application URLs [\#352](https://github.com/azavea/climate-change-api/pull/352)
- Feature/custom style sphinx [\#351](https://github.com/azavea/climate-change-api/pull/351)
- Add Rollbar error handling. [\#350](https://github.com/azavea/climate-change-api/pull/350)
- Feature/separate testing database [\#349](https://github.com/azavea/climate-change-api/pull/349)
- Indicators top-level section to docs [\#347](https://github.com/azavea/climate-change-api/pull/347)
- Feature/caching modifications [\#346](https://github.com/azavea/climate-change-api/pull/346)
- Use raw SQL to render region GeoJSON [\#342](https://github.com/azavea/climate-change-api/pull/342)
- Add SES and SQS permissions to container instance profile [\#341](https://github.com/azavea/climate-change-api/pull/341)
- Simplify region geometries on import [\#340](https://github.com/azavea/climate-change-api/pull/340)
- Fix error log storage path [\#334](https://github.com/azavea/climate-change-api/pull/334)
- Rebuild containers in CI [\#332](https://github.com/azavea/climate-change-api/pull/332)
- Retry failing jobs to a configurable limit [\#331](https://github.com/azavea/climate-change-api/pull/331)
- Add link to API Documentation [\#325](https://github.com/azavea/climate-change-api/pull/325)
- Feature/retry import from file [\#324](https://github.com/azavea/climate-change-api/pull/324)
- Enumerate valid threshold units in API [\#323](https://github.com/azavea/climate-change-api/pull/323)
- Increase Terraform memcached max size limit [\#316](https://github.com/azavea/climate-change-api/pull/316)
- Add Region Serializers, Views, Documentation [\#315](https://github.com/azavea/climate-change-api/pull/315)
- Feature/import job resume [\#314](https://github.com/azavea/climate-change-api/pull/314)
- Fill out pagination section to docs [\#313](https://github.com/azavea/climate-change-api/pull/313)
- Remove 'closes' PR template keyword [\#312](https://github.com/azavea/climate-change-api/pull/312)
- Feature/debug disable cache [\#310](https://github.com/azavea/climate-change-api/pull/310)
- Serve docs container on port 8084 [\#309](https://github.com/azavea/climate-change-api/pull/309)
- ./manage.py command to set per user custom throttling rates [\#308](https://github.com/azavea/climate-change-api/pull/308)
- Add indicator detail view [\#305](https://github.com/azavea/climate-change-api/pull/305)
- Feature/retry throttled imports [\#304](https://github.com/azavea/climate-change-api/pull/304)
- Add instructions to restore staging DBs from scratch. [\#300](https://github.com/azavea/climate-change-api/pull/300)
- Feature/selective throttling [\#289](https://github.com/azavea/climate-change-api/pull/289)
- Feature/load testing [\#281](https://github.com/azavea/climate-change-api/pull/281)
- Add Dredd endpoint testing [\#280](https://github.com/azavea/climate-change-api/pull/280)
- Clarify climate data response in docs [\#276](https://github.com/azavea/climate-change-api/pull/276)
- Update references to AWS\_ECR\_ENDPOINT in `cipublish` [\#275](https://github.com/azavea/climate-change-api/pull/275)
- Cross Year Aggregations [\#274](https://github.com/azavea/climate-change-api/pull/274)
- Iron out issues with CI tests [\#272](https://github.com/azavea/climate-change-api/pull/272)
- Update Jenkinsfile [\#271](https://github.com/azavea/climate-change-api/pull/271)
- Set models and years params defaults to 'all' for readability [\#270](https://github.com/azavea/climate-change-api/pull/270)
- Link indicator definition to how-to section in docs [\#269](https://github.com/azavea/climate-change-api/pull/269)
- Feature/staticthresholdindicator2 [\#268](https://github.com/azavea/climate-change-api/pull/268)
- Add 'making an indicator request' to docs overview [\#266](https://github.com/azavea/climate-change-api/pull/266)
- Add note about API docs to PR template [\#265](https://github.com/azavea/climate-change-api/pull/265)
- Refactor terraform configuration [\#264](https://github.com/azavea/climate-change-api/pull/264)
- API View Caching via Memcached [\#261](https://github.com/azavea/climate-change-api/pull/261)
- Remove Swagger from project [\#260](https://github.com/azavea/climate-change-api/pull/260)
- Add indicator to measure number of heatwaves per year [\#257](https://github.com/azavea/climate-change-api/pull/257)
- Change /indicator response structure to match other endpoints [\#256](https://github.com/azavea/climate-change-api/pull/256)
- Documentation request and response examples [\#255](https://github.com/azavea/climate-change-api/pull/255)
- Rebuild container before building docs [\#254](https://github.com/azavea/climate-change-api/pull/254)
- Build docs as pre-requisite of push rather than deploy [\#253](https://github.com/azavea/climate-change-api/pull/253)
- Add percentile indicators for the three base variables [\#249](https://github.com/azavea/climate-change-api/pull/249)
- Revert to upstream sphinxcontrib-openapi [\#248](https://github.com/azavea/climate-change-api/pull/248)
- Use temperature average for degree day indicators [\#242](https://github.com/azavea/climate-change-api/pull/242)
- Add docs static site creation to terraform [\#241](https://github.com/azavea/climate-change-api/pull/241)
- Indicator resource documentation [\#240](https://github.com/azavea/climate-change-api/pull/240)
- Add tests between indicator and serializer logic [\#237](https://github.com/azavea/climate-change-api/pull/237)
- Closes \#192: Add Cache-Control headers to select API resources [\#236](https://github.com/azavea/climate-change-api/pull/236)
- Feature/awf/rate limiting fix double count [\#235](https://github.com/azavea/climate-change-api/pull/235)
- Update sphinx openapi directive to use newline syntax [\#234](https://github.com/azavea/climate-change-api/pull/234)
- Feature/awf/rate limiting memcached [\#232](https://github.com/azavea/climate-change-api/pull/232)
- Quickfix 'make test' to use custom Django test settings [\#231](https://github.com/azavea/climate-change-api/pull/231)
- Closes \#208: Invalid indicator param should return 404 [\#230](https://github.com/azavea/climate-change-api/pull/230)
- Feature/awf/dev scripts to rule them all [\#229](https://github.com/azavea/climate-change-api/pull/229)
- Add climate data endpoint to docs [\#227](https://github.com/azavea/climate-change-api/pull/227)
- Add Overview: Authentication section to API docs [\#222](https://github.com/azavea/climate-change-api/pull/222)
- Feature/awf/documentation swagger one file [\#221](https://github.com/azavea/climate-change-api/pull/221)
- Feature/docs/odds and ends cleaning [\#220](https://github.com/azavea/climate-change-api/pull/220)
- Add getting started to docs [\#219](https://github.com/azavea/climate-change-api/pull/219)
- Feature/docs/auth [\#218](https://github.com/azavea/climate-change-api/pull/218)
- Closes \#193: Add Overview -- Rate Limiting to docs [\#216](https://github.com/azavea/climate-change-api/pull/216)
- Add throttling to climate data and indicator endpoints [\#215](https://github.com/azavea/climate-change-api/pull/215)
- Feature/awf/update terraform [\#211](https://github.com/azavea/climate-change-api/pull/211)
- Feature/documentation model scenario [\#210](https://github.com/azavea/climate-change-api/pull/210)
- Feature/docs/cityendpts [\#209](https://github.com/azavea/climate-change-api/pull/209)
- Add documentation for HTTP response codes [\#207](https://github.com/azavea/climate-change-api/pull/207)
- Automatically cd to shared folder dir [\#205](https://github.com/azavea/climate-change-api/pull/205)
- Closes \#190: ADR 0006 Rate Limiting [\#204](https://github.com/azavea/climate-change-api/pull/204)
- Feature/docs/params cors [\#202](https://github.com/azavea/climate-change-api/pull/202)
- Add documentation for versioning [\#201](https://github.com/azavea/climate-change-api/pull/201)
- Remove raw daily indicators [\#199](https://github.com/azavea/climate-change-api/pull/199)
- Quarterly and User Defined Aggregations [\#197](https://github.com/azavea/climate-change-api/pull/197)
- ADR0005: API Documentation + Testing [\#176](https://github.com/azavea/climate-change-api/pull/176)
- API Documentation starter [\#175](https://github.com/azavea/climate-change-api/pull/175)
- Fix broken city tests from \#161 [\#168](https://github.com/azavea/climate-change-api/pull/168)
- Refactor Time Aggregation [\#162](https://github.com/azavea/climate-change-api/pull/162)
- Closes \#153: Swap city/cityboundary OneToOneField to fix cascade delete [\#161](https://github.com/azavea/climate-change-api/pull/161)
- Degree Day unit tests [\#160](https://github.com/azavea/climate-change-api/pull/160)
- Indicator Parameters [\#158](https://github.com/azavea/climate-change-api/pull/158)
- Add missing migration for ClimateDataBaseline [\#156](https://github.com/azavea/climate-change-api/pull/156)
- Reduce Vagrant VM memory to 4Gb [\#155](https://github.com/azavea/climate-change-api/pull/155)
- Degree Days Indicators [\#154](https://github.com/azavea/climate-change-api/pull/154)
- Add merge migration to fix dangling leaf migrations [\#152](https://github.com/azavea/climate-change-api/pull/152)
- Catch KeyError exceptions in census boundary\_from\_point [\#151](https://github.com/azavea/climate-change-api/pull/151)
- Add City boundaries [\#147](https://github.com/azavea/climate-change-api/pull/147)
- Percentile Indicators [\#146](https://github.com/azavea/climate-change-api/pull/146)
- Allow cities to have additional fields in projectschema.json [\#145](https://github.com/azavea/climate-change-api/pull/145)
- Add region model and importer for regions [\#143](https://github.com/azavea/climate-change-api/pull/143)
- Feature/addtl indicator aggregations [\#142](https://github.com/azavea/climate-change-api/pull/142)
- Add ADR for API documentation [\#141](https://github.com/azavea/climate-change-api/pull/141)
- Allow population data to be added to existing cities [\#140](https://github.com/azavea/climate-change-api/pull/140)
- Add validator for UserProject [\#129](https://github.com/azavea/climate-change-api/pull/129)
- Add CORS methods [\#128](https://github.com/azavea/climate-change-api/pull/128)
- Add migration to correct related name for historic average [\#125](https://github.com/azavea/climate-change-api/pull/125)
- Feature/refactor count indicator queries [\#124](https://github.com/azavea/climate-change-api/pull/124)
- Add UserProjects [\#121](https://github.com/azavea/climate-change-api/pull/121)
- Make city search match on 'admin' [\#120](https://github.com/azavea/climate-change-api/pull/120)
- Generate historic summary data locally [\#119](https://github.com/azavea/climate-change-api/pull/119)
- Monthly aggregation indicators [\#118](https://github.com/azavea/climate-change-api/pull/118)
- Bugfix: Fix lost call to record\_precipitation\_baselines in import historic [\#117](https://github.com/azavea/climate-change-api/pull/117)
- Update unit documentation [\#112](https://github.com/azavea/climate-change-api/pull/112)
- Add HWDI \(Heat Wave Duration Index\) Indicator [\#110](https://github.com/azavea/climate-change-api/pull/110)
- Add Extreme Precipitation Events data and indicator [\#107](https://github.com/azavea/climate-change-api/pull/107)
- Closes \#95: Disable signup [\#106](https://github.com/azavea/climate-change-api/pull/106)
- Add e-mail as user id [\#105](https://github.com/azavea/climate-change-api/pull/105)
- Cleanup indicator API response [\#103](https://github.com/azavea/climate-change-api/pull/103)
- Feature/heat wave duration index [\#102](https://github.com/azavea/climate-change-api/pull/102)
- Add historical scenario [\#94](https://github.com/azavea/climate-change-api/pull/94)
- Add time aggregation level to Indicator class to\_dict [\#93](https://github.com/azavea/climate-change-api/pull/93)
- Add GitHub pull request template [\#92](https://github.com/azavea/climate-change-api/pull/92)
- Adjust count indicators for min/max avg [\#91](https://github.com/azavea/climate-change-api/pull/91)
- Skip null data points on remote import [\#88](https://github.com/azavea/climate-change-api/pull/88)
- Fix total precip indicator units confusion [\#86](https://github.com/azavea/climate-change-api/pull/86)
- Return avg, min and max values with yearly indicator [\#85](https://github.com/azavea/climate-change-api/pull/85)
- Add labels to indicators [\#84](https://github.com/azavea/climate-change-api/pull/84)
- Add indicators for wrapping raw daily data [\#83](https://github.com/azavea/climate-change-api/pull/83)
- Fix issue using tuple as function [\#82](https://github.com/azavea/climate-change-api/pull/82)
- Add merge migration to resolve hanging leafs [\#79](https://github.com/azavea/climate-change-api/pull/79)
- Implement existing yearly indicators [\#78](https://github.com/azavea/climate-change-api/pull/78)
- Add custom ObtainAuthToken view for Climate API [\#77](https://github.com/azavea/climate-change-api/pull/77)
- Implement temperature conversion [\#76](https://github.com/azavea/climate-change-api/pull/76)
- Add ADR for authentication methods [\#75](https://github.com/azavea/climate-change-api/pull/75)
- Feature/model labels [\#74](https://github.com/azavea/climate-change-api/pull/74)
- Closes \#64: Deleting a ClimateDataCell should not delete cities [\#73](https://github.com/azavea/climate-change-api/pull/73)
- Closes \#63: Expose map cell lat/lon in CitySerializer [\#72](https://github.com/azavea/climate-change-api/pull/72)
- Feature/tweak ecs management task [\#67](https://github.com/azavea/climate-change-api/pull/67)
- Feature/improve import mem speed [\#66](https://github.com/azavea/climate-change-api/pull/66)
- ClimateData Optimization [\#65](https://github.com/azavea/climate-change-api/pull/65)
- Add import from staging [\#61](https://github.com/azavea/climate-change-api/pull/61)
- Feature/city search [\#60](https://github.com/azavea/climate-change-api/pull/60)
- Feature/per user dev queues [\#59](https://github.com/azavea/climate-change-api/pull/59)
- Feature/indicator api endpoint [\#56](https://github.com/azavea/climate-change-api/pull/56)
- Fixup importer lat/lon -\> index transformation [\#55](https://github.com/azavea/climate-change-api/pull/55)
- Add test command to project Makefile [\#54](https://github.com/azavea/climate-change-api/pull/54)
- Always allow SessionAuth and BrowsableAPI [\#53](https://github.com/azavea/climate-change-api/pull/53)
- Add confirmation modal for replacing API token [\#48](https://github.com/azavea/climate-change-api/pull/48)
- Redirect from root to user profile [\#47](https://github.com/azavea/climate-change-api/pull/47)
- Use https for links in user management emails [\#45](https://github.com/azavea/climate-change-api/pull/45)
- Implement changes to allow logging in AWS [\#43](https://github.com/azavea/climate-change-api/pull/43)
- Set ALLOWED\_HOSTS via terraform [\#41](https://github.com/azavea/climate-change-api/pull/41)
- Feature/adrs [\#40](https://github.com/azavea/climate-change-api/pull/40)
- Collate data points by source data cell [\#38](https://github.com/azavea/climate-change-api/pull/38)
- Add min/max aggregation of model data [\#37](https://github.com/azavea/climate-change-api/pull/37)
- Use NetCDF library to load data [\#35](https://github.com/azavea/climate-change-api/pull/35)
- Speed up nearest city query [\#33](https://github.com/azavea/climate-change-api/pull/33)
- Fixes up the API so that all the views work again [\#32](https://github.com/azavea/climate-change-api/pull/32)
- Process jobs [\#31](https://github.com/azavea/climate-change-api/pull/31)
- Save static assets to S3 [\#30](https://github.com/azavea/climate-change-api/pull/30)
- Feature/swagger docs [\#28](https://github.com/azavea/climate-change-api/pull/28)
- Fix failing tests by setting up test auth and login [\#27](https://github.com/azavea/climate-change-api/pull/27)
- Add initial notes from 2016-06-08 advisory board mtg [\#25](https://github.com/azavea/climate-change-api/pull/25)
- Feature/api data view [\#24](https://github.com/azavea/climate-change-api/pull/24)
- Update Django to use Amazon SES email backend when not in DEBUG [\#22](https://github.com/azavea/climate-change-api/pull/22)
- Override django-admin with django-registration password reset [\#21](https://github.com/azavea/climate-change-api/pull/21)
- Set up token auth and rewrite views to classes [\#20](https://github.com/azavea/climate-change-api/pull/20)
- Add SQS and create\_jobs management command [\#19](https://github.com/azavea/climate-change-api/pull/19)
- Feature/scenario views [\#17](https://github.com/azavea/climate-change-api/pull/17)
- Add editable user profile page [\#16](https://github.com/azavea/climate-change-api/pull/16)
- Profile model [\#12](https://github.com/azavea/climate-change-api/pull/12)
- Add deployment [\#10](https://github.com/azavea/climate-change-api/pull/10)
- Feature/sphinx [\#9](https://github.com/azavea/climate-change-api/pull/9)
- Feature/setup tests [\#8](https://github.com/azavea/climate-change-api/pull/8)
- Add Django Rest Framework with basic ClimateDataViewSet [\#6](https://github.com/azavea/climate-change-api/pull/6)
- Bump django to 1.9.6 [\#5](https://github.com/azavea/climate-change-api/pull/5)
- Add import cities management command [\#4](https://github.com/azavea/climate-change-api/pull/4)
- Add models for city and data [\#3](https://github.com/azavea/climate-change-api/pull/3)
- Add development environment [\#1](https://github.com/azavea/climate-change-api/pull/1)



* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*