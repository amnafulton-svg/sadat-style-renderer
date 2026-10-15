// "Why Did the US Get Rich But Latin America Never Did" (359.1 s narration, no title: it starts on the first word).
// Same grammar as quincy.tsx: film for concrete statements, prints on a wall/paper for named things,
// type on black/concrete for the argument. Pictures change on a sentence end or pause; rhythmic lists cut per item.
// Times are whisper word starts from words.json (narration seconds).
import React from 'react';
import {Film, FilmProps} from '../layers/Film';
import {Black, ConcreteWall, Paper} from '../layers/Backgrounds';
import {BlackTag, DateTag, NameStrip, PhotoPrint} from '../layers/Print';
import {BigSerif, GhostTitle, Highlight, LabelTape, ListWords, QuoteText} from '../layers/Type';
import {Chart, DocCard, DocMap} from '../layers/Evidence';
import {EnterKind} from '../transitions';
import media from '../lib/media.json';

export type Scene = {id: string; from: number; to: number; enter: EnterKind; why: string; el: React.ReactNode};

const q = (s: string, t0: number[]) => s.split(' ').map((w, i) => ({w, at: t0[i]}));
const l = (s: string, t0: number[]) => s.split('|').map((w, i) => ({w, at: t0[i]}));

// house rule: 4:3 film is never zoomed to fill — anything narrower than 1.7:1 is padded automatically
const M = media as Record<string, {w: number; h: number; d: number}>;
const F: React.FC<FilmProps> = (p) => <Film fit={M[p.src] && M[p.src].w / M[p.src].h < 1.7 ? 'pad' : 'fill'} {...p} />;

const CREAM = '#f2ead8';
const HL = {x: 960, y: 900}; // highlight bar under footage

export const END = 360.6; // narration ends 358.3; hold, then fade

export const SCENES: Scene[] = [
  // ================= HOOK =================
  {id: 'h_1700', from: 0, to: 3.52, enter: 'rack', why: '"Picture this. The year is 1700." — a living colonial street, the year stamped on its word.',
    el: <><F src="colonial_cuzco20s_street.mp4" start={0} grade="sepia" /><BigSerif text="1700" at={2.08} x={960} y={520} size={260} color={CREAM} /></>},
  {id: 'h_northsouth', from: 3.52, to: 8.74, enter: 'cut', why: 'North vs south side by side — you could barely tell them apart.',
    el: (
      <Paper>
        <PhotoPrint src="ind_mexcity1800_0.jpg" at={4.5} x={530} y={520} w={760} rot={-2.5} from="left" grade="warm" />
        <PhotoPrint src="ind_philly1800_1.jpg" at={5.24} x={1390} y={540} w={760} rot={2} from="right" grade="warm" />
        <LabelTape text="SOUTH" at={7.74} x={530} y={880} size={46} />
        <LabelTape text="NORTH" at={7.28} x={1390} y={890} size={46} rot={1.5} />
      </Paper>
    )},
  {id: 'h_mexcity', from: 8.74, to: 14.48, enter: 'cut', why: 'Mexico City named: the 1695 Plaza Mayor, and the three comparatives land as a list.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_plaza_mayor_1695.jpg" at={8.9} x={1320} y={520} w={940} rot={1.5} from="right" grade="warm" />
        <BlackTag at={9.1} x={1300} y={880} line1="Mexico City" line2="Plaza Mayor, 1695" />
        <ListWords anchor="left" x={110} y={560} size={84} color={CREAM} items={l('Richer.|Grander.|More populated.', [9.7, 10.46, 11.16])} />
      </ConcreteWall>
    )},
  {id: 'h_potosi', from: 14.48, to: 19.46, enter: 'cut', why: '"The silver mines of Potosí" — the 1590 engraving of the mountain itself.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_debry_potosi_1590.jpg" at={14.6} x={960} y={500} w={1160} rot={-1} from="bottom" />
        <BlackTag at={15.24} x={1300} y={830} line1="Potosí" line2="silver mountain, 1590" />
        <Highlight text="MORE WEALTH THAN ANY COLONY IN HISTORY" at={16.38} x={960} y={960} size={52} />
      </ConcreteWall>
    )},
  {id: 'h_us', from: 19.46, to: 24.16, enter: 'cut', why: '"Three centuries later… the wealthiest nation on Earth" — 1930 Manhattan waterfront.',
    el: <><F src="commodity_nyc_pier.mp4" start={0} grade="bw" /><Highlight text="THE WEALTHIEST NATION ON EARTH" at={22.68} {...HL} /></>},
  {id: 'h_trapped', from: 24.16, to: 28.62, enter: 'cut', why: '"Trapped in cycles of poverty, debt and political chaos" — favela, the list ticks in.',
    el: <><F src="coldwar_brazil_favela2.mp4" start={0} grade="warm" /><ListWords anchor="left" x={120} y={560} size={80} color={CREAM} dim={false} items={l('poverty.|debt.|political chaos.', [26.74, 27.4, 27.86])} /></>},
  {id: 'h_question', from: 28.62, to: 30.9, enter: 'cut', why: 'The question alone on black — the beat before the thesis.',
    el: <Black><QuoteText x={960} y={540} size={86} width={1300} color={CREAM} words={q('So what actually happened?', [28.62, 28.94, 29.62, 29.92])} mark={['happened?']} /></Black>},
  {id: 'h_map', from: 30.9, to: 37.4, enter: 'whip', why: '"Two halves of the same hemisphere" — the Americas, north lit on "two", south on "halves".',
    el: <DocMap id={1} spec={{mode: 'territory', title: 'One hemisphere, two halves', year: '1700',
      tilt: {from: 16, to: 8},
      camera: {fromCenter: [-80, 14], fromZoom: 1.85, center: [-78, 8], zoom: 1.95},
      territories: [
        {id: 'north', name: 'NORTH', color: '#e8c35a', countries: ['United States of America', 'Canada'], appearAt: 31.18},
        {id: 'south', name: 'SOUTH', color: '#9e1b1b', countries: ['Mexico', 'Guatemala', 'Belize', 'Honduras', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama', 'Cuba', 'Dominican Rep.', 'Haiti', 'Colombia', 'Venezuela', 'Ecuador', 'Peru', 'Bolivia', 'Brazil', 'Paraguay', 'Uruguay', 'Argentina', 'Chile', 'Guyana', 'Suriname'], appearAt: 31.44},
      ],
      places: [
        {label: 'Mexico City', coordinates: [-99.13, 19.43], labelPosition: 'left', appearAt: 33.0},
        {label: 'Potosí', coordinates: [-65.75, -19.58], labelPosition: 'right', appearAt: 33.68},
        {label: 'Boston', coordinates: [-71.06, 42.36], labelPosition: 'right', appearAt: 34.12},
      ],
      regions: [
        {label: 'North', coordinates: [-100, 40], size: 64, italic: false, appearAt: 31.18},
        {label: 'South', coordinates: [-58, -8], size: 64, italic: false, appearAt: 31.44},
      ]}} />},
  {id: 'h_answer', from: 37.4, to: 41.54, enter: 'cut', why: 'Three negations, each its own line — "not luck, not race, not even culture".',
    el: (
      <ConcreteWall>
        <GhostTitle text="THE ANSWER" x={960} y={260} size={220} />
        <ListWords x={960} y={600} size={84} color={CREAM} items={l("isn't luck.|isn't race.|isn't even culture.", [38.1, 39.22, 40.52])} />
      </ConcreteWall>
    )},
  {id: 'h_structural', from: 41.54, to: 44.98, enter: 'cut', why: '"Something far more structural" — Inca stone under Spanish building: the theme in one picture.',
    el: <><F src="colonial_peru37_sacsay_ruins.mp4" start={0} grade="sepia" /><Highlight text="STRUCTURAL" at={42.52} {...HL} size={80} /></>},

  // ================= COLONIAL =================
  {id: 'c_conquest', from: 44.98, to: 50.14, enter: 'cut', why: '"When the Spanish arrived in the early 1500s" — the conquest of Tenochtitlan painting.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_conquest_tenochtitlan.jpg" at={45.2} x={960} y={500} w={1240} rot={1} from="fade" grade="warm" />
        <DateTag text="early 1500s" at={46.16} x={1420} y={900} />
      </ConcreteWall>
    )},
  {id: 'c_market', from: 50.14, to: 54.48, enter: 'cut', why: 'Dense native population still there in the 1930s market.', el: <F src="colonial_peru37_market.mp4" start={0} grade="sepia" />},
  {id: 'c_empires', from: 54.48, to: 58.48, enter: 'cut', why: 'The two empires named: Aztec map of Tenochtitlan and the Inca in Guaman Poma.',
    el: (
      <Paper>
        <PhotoPrint src="colonial_tenochtitlan_map_1524.jpg" at={54.6} x={560} y={500} w={760} rot={-2} from="left" />
        <PhotoPrint src="colonial_guaman_poma_inca_mummy.jpg" at={55.2} x={1380} y={520} w={600} rot={2.5} from="right" />
        <LabelTape text="AZTEC" at={54.76} x={560} y={900} size={46} />
        <LabelTape text="INCA" at={55.32} x={1380} y={920} size={46} rot={1.5} />
      </Paper>
    )},
  {id: 'c_hijack', from: 58.48, to: 62.9, enter: 'cut', why: 'Cities, agriculture, labor systems — list over Inca wall, HIJACK lands on the verb.',
    el: (
      <>
        <F src="colonial_inca_cuzco_wall.mp4" start={0} grade="sepia" />
        <ListWords anchor="left" x={120} y={480} size={76} color={CREAM} dim={false} items={l('Cities.|Agriculture.|Labor systems.', [58.6, 59.3, 60.1])} />
        <Highlight text="HIJACK" at={61.84} {...HL} size={80} />
      </>
    )},
  {id: 'c_pizarro', from: 62.9, to: 66.4, enter: 'cut', why: 'The conquistador named once; the year of the find lands beside him.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_pizarro_portrait.jpg" at={62.95} x={620} y={500} w={600} rot={-1.5} from="bottom" />
        <BlackTag at={63.1} x={760} y={880} line1="Francisco Pizarro" line2="conquistador" />
        <BigSerif text="1545" at={64.84} x={1360} y={500} size={260} color={CREAM} />
      </ConcreteWall>
    )},
  {id: 'c_cerro', from: 66.4, to: 74.58, enter: 'cut', why: 'Cerro Rico named, then the coin it minted; the superlative as a bar.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_cerro_rico.jpg" at={66.6} x={760} y={470} w={1040} rot={-1.5} from="left" />
        <BlackTag at={66.86} x={300} y={830} line1="Cerro Rico" line2="Potosí, Bolivia" align="left" />
        <PhotoPrint src="colonial_cob_coin_8reales.jpg" at={70.24} x={1480} y={520} w={480} rot={4} from="right" />
        <Highlight text="THE MOST PRODUCTIVE MINE IN HUMAN HISTORY" at={71.54} x={960} y={965} size={52} />
      </ConcreteWall>
    )},
  {id: 'c_mita', from: 74.58, to: 82.7, enter: 'cut', why: 'The mita: forced labor in the mine, then Guaman Poma\'s drawing of the abuse.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_potosi_mine_workers.jpg" at={74.8} x={700} y={520} w={980} rot={1.5} from="bottom" />
        <LabelTape text="THE MITA" at={77.7} x={560} y={900} size={52} />
        <PhotoPrint src="colonial_guaman_poma_page.jpg" at={78.36} x={1450} y={540} w={560} rot={-3} from="right" />
      </ConcreteWall>
    )},
  {id: 'c_doorway', from: 82.7, to: 85.04, enter: 'cut', why: 'Breath: a colonial doorway in Cuzco.', el: <F src="colonial_cuzco20s_doorway.mp4" start={0} grade="sepia" />},
  {id: 'c_encomienda', from: 85.04, to: 92.96, enter: 'cut', why: 'Encomienda named — the 16th-c. tribute codex of an encomendero.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="colonial_encomendero_tepetlaoztoc.jpg" at={85.1} x={960} y={500} w={1000} rot={-1} from="fade" />
        <LabelTape text="ENCOMIENDA" at={85.16} x={500} y={880} size={52} />
        <Highlight text="TRIBUTE AND LABOR" at={87.92} x={1250} y={960} size={58} />
      </ConcreteWall>
    )},
  {id: 'c_fleet', from: 92.96, to: 97.66, enter: 'cut', why: '"Pure extraction … pump wealth into Spanish royal coffers" — the silver road, Potosí to Seville, drawn on "pump".',
    el: <DocMap id={2} spec={{mode: 'journey', title: 'The silver road', year: '1600s',
      camera: {fromCenter: [-50, 4], fromZoom: 1.55, center: [-42, 8], zoom: 1.7},
      places: [
        {label: 'Potosí', coordinates: [-65.75, -19.58], labelPosition: 'below', importance: 'primary', appearAt: 93.0},
        {label: 'Seville', coordinates: [-5.98, 37.39], labelPosition: 'above', importance: 'primary', appearAt: 96.08},
      ],
      routes: [
        {id: 'mule', points: [[-65.75, -19.58], [-70.3, -18.48]], dashed: true, color: '#f2ead8', startAt: 94.64, endAt: 95.26},
        {id: 'fleet', points: [[-70.3, -18.48], [-79.6, -2], [-79.9, 9.0], [-79.5, 9.6], [-76, 13], [-82.4, 23.1], [-60, 32], [-30, 37], [-6.3, 36.8], [-5.98, 37.39]], vehicle: 'ship', color: '#c9a45c', label: 'silver fleet', startAt: 95.26, endAt: 96.72},
      ]}} />},

  // ================= NORTH =================
  {id: 'n_flip', from: 97.66, to: 99.4, enter: 'cut', why: '"Now flip north." — act change on type.',
    el: <Black><BigSerif text="NORTH" at={98.2} x={960} y={540} size={240} color={CREAM} bar /></Black>},
  {id: 'n_nothing', from: 99.4, to: 105.84, enter: 'cut', why: 'Three absences ("no gold, no silver, no labor force") as a list over the empty New England land.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="north_pilgrims_landing_bacon.jpg" at={99.5} x={1360} y={470} w={900} rot={1.5} from="right" grade="warm" />
        <BlackTag at={100.44} x={1380} y={800} line1="New England" line2="the British arrive" />
        <ListWords anchor="left" x={100} y={520} size={72} color={CREAM} items={l('No gold.|No silver.|No labor to exploit.', [101.2, 102.18, 103.16])} />
      </ConcreteWall>
    )},
  {id: 'n_cursed', from: 105.84, to: 108.88, enter: 'cut', why: '"Cursed with poverty" — empty grassland.',
    el: <><F src="north_prairie_grass2.mp4" start={0} grade="bw" /><Highlight text="CURSED WITH POVERTY" at={107.36} {...HL} /></>},
  {id: 'n_blessing', from: 108.88, to: 111.5, enter: 'cut', why: '"Their greatest blessing".',
    el: <><F src="north_prairie_grass1.mp4" start={0} grade="bw" /><Highlight text="THEIR GREATEST BLESSING" at={110.3} {...HL} /></>},
  {id: 'n_build', from: 111.5, to: 114.54, enter: 'cut', why: '"Nothing to steal — settlers had to build."',
    el: <><F src="north_plowshare.mp4" start={0} grade="bw" /><Highlight text="THEY HAD TO BUILD" at={113.2} {...HL} /></>},
  {id: 'n_fields', from: 114.54, to: 116.72, enter: 'cut', why: 'Cleared fields, founded towns (list beat).',
    el: <><F src="north_horse_team.mp4" start={0} grade="bw" /><ListWords anchor="left" x={120} y={500} size={76} color={CREAM} dim={false} items={l('Cleared fields.|Founded towns.', [114.66, 115.62])} /></>},
  {id: 'n_power', from: 116.72, to: 120.9, enter: 'cut', why: 'A political tradition that distributed power — the Mayflower Compact signing.',
    el: <ConcreteWall><PhotoPrint src="north_mayflower_compact_signing.jpg" at={116.8} x={960} y={480} w={1000} rot={-1} from="bottom" /><Highlight text="POWER DISTRIBUTED, NOT CONCENTRATED" at={118.14} x={960} y={960} size={54} /></ConcreteWall>},
  {id: 'n_1619', from: 120.9, to: 127.88, enter: 'cut', why: '1619 and the House of Burgesses, the first elected legislature in the New World.',
    el: (
      <ConcreteWall>
        <BigSerif text="1619" at={121.0} x={430} y={420} size={220} color={CREAM} sub="Virginia" />
        <PhotoPrint src="north_burgesses_first_assembly.jpg" at={123.64} x={1270} y={470} w={1060} rot={1.5} from="right" />
        <BlackTag at={123.9} x={1330} y={830} line1="House of Burgesses" line2="Jamestown, 1619" />
        <Highlight text="FIRST ELECTED LEGISLATURE IN THE NEW WORLD" at={125.38} x={960} y={970} size={48} />
      </ConcreteWall>
    )},
  {id: 'n_town', from: 127.88, to: 133.84, enter: 'cut', why: 'Town meetings, assemblies, property rights — a print per item.',
    el: (
      <Paper>
        <PhotoPrint src="north_green_dragon_boston.jpg" at={128.64} x={420} y={440} w={620} rot={-2.5} from="left" />
        <PhotoPrint src="north_new_england_church.jpg" at={129.88} x={980} y={500} w={520} rot={1.5} from="bottom" />
        <PhotoPrint src="north_old_new_england_house.jpg" at={131.12} x={1500} y={450} w={580} rot={-1} from="right" />
        <LabelTape text="TOWN MEETINGS" at={128.64} x={420} y={790} size={40} />
        <LabelTape text="LOCAL ASSEMBLIES" at={129.88} x={980} y={880} size={40} rot={1.5} />
        <LabelTape text="PROPERTY RIGHTS" at={131.12} x={1500} y={800} size={40} />
      </Paper>
    )},
  {id: 'n_nobel', from: 133.84, to: 142.3, enter: 'cut', why: 'The three economists, each print on his name; the Nobel after.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="north_acemoglu_portrait.jpg" at={134.34} x={400} y={430} w={460} rot={-2} from="left" grade="none" />
        <PhotoPrint src="north_johnson_portrait.jpg" at={135.64} x={960} y={430} w={460} rot={1} from="bottom" grade="none" />
        <PhotoPrint src="north_robinson_johnson_press.jpg" at={136.68} x={1520} y={430} w={460} rot={-1} from="right" grade="none" objectPosition="80% 40%" aspect={0.8} />
        <NameStrip text="Daron Acemoglu" at={134.34} x={400} y={760} rot={-1.5} />
        <NameStrip text="Simon Johnson" at={135.64} x={960} y={770} rot={1} />
        <NameStrip text="James Robinson" at={136.68} x={1520} y={760} rot={-1} />
        <Highlight text="2024 NOBEL PRIZE IN ECONOMICS" at={138.16} x={960} y={960} size={60} />
      </ConcreteWall>
    )},
  {id: 'n_inclusive', from: 142.3, to: 146.44, enter: 'cut', why: 'The key distinction as two words.',
    el: (
      <Black>
        <Highlight text="INCLUSIVE" at={143.54} x={560} y={540} size={96} />
        <BigSerif text="vs" at={144.12} x={960} y={520} size={80} color={CREAM} />
        <Highlight text="EXTRACTIVE" at={144.48} x={1380} y={540} size={96} />
      </Black>
    )},
  {id: 'n_invites', from: 146.44, to: 149.5, enter: 'cut', why: '"One invites broad participation and investment."',
    el: <><F src="north_wagon_team.mp4" start={0} grade="bw" /><Highlight text="BROAD PARTICIPATION" at={147.2} {...HL} /></>},
  {id: 'n_hoards', from: 149.5, to: 153.2, enter: 'cut', why: '"The other hoards wealth at the top" — a colonial palace.',
    el: <><F src="colonial_lapaz_palace.mp4" start={0} grade="sepia" /><Highlight text="HOARDS WEALTH AT THE TOP" at={149.9} {...HL} /></>},

  // ================= INDEPENDENCE =================
  {id: 'i_1700', from: 153.2, to: 157.58, enter: 'cut', why: 'Time jump on black.',
    el: <Black><BigSerif text="1700" at={153.34} x={960} y={500} size={260} color={CREAM} sub="two models, quietly diverging" /></Black>},
  {id: 'i_1800', from: 157.58, to: 158.8, enter: 'cut', why: 'Second year card.', el: <Black><BigSerif text="1800" at={157.7} x={960} y={500} size={260} color={CREAM} /></Black>},
  {id: 'i_half', from: 158.8, to: 166.5, enter: 'cut', why: '"Mexico GDP per capita had fallen to roughly half of the United States … a century earlier neck and neck" — the line falls to half on "half", then 1700 is marked on "neck and neck".',
    el: <Chart chart={{type: 'line', kicker: 'GDP per capita · % of the US', title: 'Mexico vs the United States', appear: 158.8,
      format: {suffix: '%'}, runningTag: false, x: [1700, 1815], y: [0, 120], xTicks: [1700, 1750, 1800], yTicks: [25, 50, 75, 100],
      series: [
        {label: 'MEXICO', points: [[1700, 100], [1800, 50]], color: 'gold'},
        {label: 'UNITED STATES', points: [[1700, 100], [1800, 100]], color: 'cream'},
      ],
      reveal: [{x: 1800, at: 161.3}],
      callouts: [{x: 1800, series: 0, text: 'HALF', at: 161.5}],
      markers: [{x: 1700, label: 'NECK AND NECK', at: 165.46}]}} />},
  {id: 'i_hidalgo', from: 166.5, to: 170.74, enter: 'dissolve', why: 'Independence begins: Hidalgo named.',
    el: (
      <ConcreteWall>
        <PhotoPrint src="ind_hidalgo_0.jpg" at={166.7} x={760} y={500} w={760} rot={-1.5} from="bottom" grade="warm" />
        <NameStrip text="Miguel Hidalgo" at={167.0} x={1400} y={420} />
        <Highlight text="A GREAT RESET?" at={169.48} x={1300} y={900} size={60} />
      </ConcreteWall>
    )},
  {id: 'i_boyaca', from: 170.74, to: 174.1, enter: 'cut', why: 'Instead: catastrophe — battle painting.',
    el: <ConcreteWall><PhotoPrint src="ind_boyaca_2.jpg" at={170.8} x={960} y={500} w={1200} rot={1} from="fade" grade="warm" /><Highlight text="CATASTROPHE" at={172.6} x={960} y={960} size={70} /></ConcreteWall>},
  {id: 'i_wars', from: 174.1, to: 177.84, enter: 'cut', why: 'Wars of independence, dated.',
    el: <ConcreteWall><PhotoPrint src="ind_carabobo_2.jpg" at={174.2} x={960} y={500} w={1200} rot={-1} from="right" grade="warm" /><DateTag text="1808–1826" at={176.16} x={1420} y={920} /></ConcreteWall>},
  {id: 'i_shattered', from: 177.84, to: 180.92, enter: 'cut', why: 'List of damage (1).',
    el: <ConcreteWall><PhotoPrint src="ind_ayacucho_0.jpg" at={177.9} x={1390} y={500} w={860} rot={1.5} from="right" grade="warm" /><ListWords anchor="left" x={100} y={560} size={70} color={CREAM} items={l('Shattered populations.|Drained treasuries.', [177.84, 179.62])} /></ConcreteWall>},
  {id: 'i_flooded', from: 180.92, to: 184.02, enter: 'cut', why: 'List of damage (2): flooded mines, a vacuum.',
    el: <ConcreteWall><PhotoPrint src="ind2_valenciana_3.jpg" at={181.0} x={1390} y={500} w={860} rot={-1.5} from="right" grade="warm" /><ListWords anchor="left" x={100} y={560} size={70} color={CREAM} items={l('Flooded silver mines.|A political vacuum.', [180.92, 182.5])} /></ConcreteWall>},
  {id: 'i_caudillos', from: 184.02, to: 190.22, enter: 'cut', why: 'Caudillos: strongmen thrown onto the board one by one.',
    el: (
      <Paper>
        <PhotoPrint src="ind_santaanna_0.jpg" at={184.5} x={330} y={420} w={420} rot={-3} from="left" grade="warm" />
        <PhotoPrint src="ind_rosas_4.jpg" at={185.0} x={760} y={460} w={420} rot={2} from="bottom" grade="warm" />
        <PhotoPrint src="ind_paez_2.jpg" at={185.5} x={1180} y={420} w={420} rot={-1.5} from="bottom" grade="warm" />
        <PhotoPrint src="ind_gaucho_0.jpg" at={187.3} x={1600} y={470} w={420} rot={3} from="right" grade="warm" />
        <PhotoPrint src="ind2_francia_0.jpg" at={188.52} x={960} y={700} w={380} rot={-2} from="bottom" grade="warm" />
        <NameStrip text="Santa Anna" sub="Mexico" at={184.7} x={330} y={650} rot={-2} size={28} />
        <NameStrip text="Rosas" sub="Argentina" at={185.2} x={640} y={700} rot={2} size={28} />
        <NameStrip text="Páez" sub="Venezuela" at={185.7} x={1290} y={655} rot={-1.5} size={28} />
        <NameStrip text="Francia" sub="Paraguay" at={188.7} x={960} y={905} rot={1} size={28} />
        <LabelTape text="CAUDILLOS" at={185.52} x={330} y={800} size={50} />
        <Highlight text="RULING BY FORCE" at={188.52} x={1500} y={930} size={58} />
      </Paper>
    )},
  {id: 'i_10', from: 190.22, to: 193.68, enter: 'cut', why: '"Bolivia wrote 10 different constitutions" — its first one, 1826, the title marked on "constitutions".',
    el: <DocCard photo="bolivia_1826.jpg" aspect={0.8806} at={190.3} source="Constitución de 1826 · Bolivia"
      marks={[{box: [0.1458, 0.0212, 0.8314, 0.0915], at: 191.84, until: 192.6}]} />},
  {id: 'i_8', from: 193.68, to: 196.56, enter: 'cut', why: '"Ecuador and Peru each wrote eight" — the two countries lit on their names, Bolivia beside them.',
    el: <DocMap id={3} spec={{mode: 'territory', title: 'Eight constitutions each', year: '19th century',
      camera: {fromCenter: [-73, -9], fromZoom: 4.6, center: [-73, -9], zoom: 4.9},
      territories: [
        {id: 'ecuador', name: 'ECUADOR · 8', color: '#9e1b1b', countries: ['Ecuador'], appearAt: 193.68},
        {id: 'peru', name: 'PERU · 8', color: '#9e1b1b', countries: ['Peru'], appearAt: 194.84},
        {id: 'bolivia', name: 'BOLIVIA · 10', color: '#c9a45c', countries: ['Bolivia'], appearAt: 193.68},
      ],
      regions: [
        {label: 'Ecuador · 8', coordinates: [-79.2, -0.6], size: 18, italic: false, appearAt: 193.9},
        {label: 'Peru · 8', coordinates: [-75.2, -9.6], size: 26, italic: false, appearAt: 194.84},
        {label: 'Bolivia · 10', coordinates: [-64.6, -16.8], size: 22, italic: false, appearAt: 193.9},
      ]}} />},
  {id: 'i_foreign', from: 196.56, to: 201.5, enter: 'cut', why: 'Democracy as a foreign idea.',
    el: <ConcreteWall><PhotoPrint src="ind_boyaca_1.jpg" at={196.7} x={960} y={500} w={1100} rot={1} from="bottom" grade="warm" /><Highlight text="A FOREIGN IDEA" at={200.16} x={960} y={960} size={66} /></ConcreteWall>},
  {id: 'i_homestead', from: 201.5, to: 210.1, enter: 'whip', why: 'Meanwhile: the Homestead Act itself (NARA) — its title marked on "Homestead Act", then "one hundred and sixty acres" on the spoken "160 acres".',
    el: <DocCard photo="homestead_act.jpg" aspect={0.7339} at={201.6} source="National Archives · Act of May 20, 1862"
      marks={[
        {box: [0.1094, 0.2422, 0.898, 0.279], at: 203.46, until: 204.6},
        {box: [0.4255, 0.8981, 0.8612, 0.9205], at: 205.94, until: 207.2},
      ]} />},
  {id: 'i_stake', from: 210.1, to: 213.56, enter: 'cut', why: '"A stake in the future" — a homesteading family in front of their house (Butcher).',
    el: <ConcreteWall><PhotoPrint src="north_butcher_schreyer_house.jpg" at={210.2} x={960} y={480} w={1000} rot={-1} from="bottom" grade="bw" /><Highlight text="A STAKE IN THE FUTURE" at={212.0} x={960} y={960} size={64} /></ConcreteWall>},
  {id: 'i_broken', from: 213.56, to: 216.84, enter: 'cut', why: '"The other was … a broken empire."',
    el: <ConcreteWall><PhotoPrint src="ind2_maipu_2.jpg" at={213.6} x={960} y={500} w={1150} rot={-1} from="fade" grade="warm" /><Highlight text="A BROKEN EMPIRE" at={215.74} x={960} y={960} size={66} /></ConcreteWall>},

  // ================= COMMODITY =================
  {id: 'k_title', from: 216.84, to: 218.3, enter: 'cut', why: 'Act title.',
    el: <ConcreteWall><GhostTitle text="COMMODITY" x={960} y={400} size={220} /><Highlight text="THE COMMODITY TRAP" at={217.58} x={960} y={620} size={80} /></ConcreteWall>},
  {id: 'k_train', from: 218.3, to: 220.36, enter: 'cut', why: 'Export trains.', el: <F src="commodity_bz_train.mp4" start={0} grade="bw" />},
  {id: 'k_crates', from: 220.36, to: 225.52, enter: 'cut', why: 'Single-crop economies.',
    el: <><F src="commodity_bz_crates.mp4" start={0} grade="bw" /><Highlight text="SINGLE CROPS" at={223.12} {...HL} /></>},
  {id: 'k_cuba', from: 225.52, to: 227.04, enter: 'whip', why: 'List montage: one crop per country.',
    el: <><F src="commodity_cuba_cutting.mp4" start={0} grade="bw" /><BlackTag at={225.6} x={1450} y={880} line1="Cuba" line2="sugar" /></>},
  {id: 'k_brazil', from: 227.04, to: 228.46, enter: 'whip', why: 'List montage.',
    el: <><F src="commodity_cof_tarp.mp4" start={0} grade="bw" /><BlackTag at={227.1} x={1450} y={880} line1="Brazil" line2="coffee" /></>},
  {id: 'k_chile', from: 228.46, to: 229.86, enter: 'whip', why: 'List montage.',
    el: <><F src="commodity_chile_pit_a.mp4" start={0} grade="bw" /><BlackTag at={228.5} x={1450} y={880} line1="Chile" line2="copper" /></>},
  {id: 'k_bananas', from: 229.86, to: 231.9, enter: 'whip', why: 'List montage.',
    el: <><F src="commodity_ban_plantation.mp4" start={0} grade="bw" /><BlackTag at={229.9} x={1450} y={880} line1="Central America" line2="bananas" /></>},
  {id: 'k_ufco', from: 231.9, to: 235.2, enter: 'cut', why: 'United Fruit named — its own 1935 menu.',
    el: <ConcreteWall><PhotoPrint src="commodity_gwf_menu.jpg" at={232.0} x={900} y={520} w={700} rot={-2} from="bottom" /><BlackTag at={233.42} x={1240} y={800} line1="United Fruit Company" line2="Great White Fleet" /></ConcreteWall>},
  {id: 'k_republics', from: 235.2, to: 238.42, enter: 'cut', why: 'Bananas loaded onto ships — "banana republics".',
    el: <><F src="commodity_ban_load.mp4" start={0} grade="bw" /><Highlight text="BANANA REPUBLICS" at={236.94} {...HL} /></>},
  {id: 'k_nyc', from: 238.42, to: 242.56, enter: 'cut', why: 'Profits flowing to Boston and New York.',
    el: <><F src="commodity_nyc_down.mp4" start={0} grade="bw" /><BlackTag at={240.94} x={1450} y={880} line1="Boston · New York" line2="where the profits went" /></>},
  {id: 'k_boom', from: 242.56, to: 245.34, enter: 'cut', why: 'Coffee exchange in Santos — boom.',
    el: <><F src="commodity_cof_santos.mp4" start={0} grade="bw" /><Highlight text="BOOM" at={244.56} {...HL} size={90} /></>},
  {id: 'k_bust', from: 245.34, to: 248.66, enter: 'cut', why: 'Bust: the 1929 headline.', el: <F src="commodity_ws_nyt.mp4" start={0} rate={0.9} grade="bw" />},
  {id: 'k_nobase', from: 248.66, to: 251.0, enter: 'cut', why: 'No industrial base.',
    el: <><F src="commodity_cof_woman.mp4" start={0} grade="bw" /><Highlight text="NO INDUSTRIAL BASE" at={249.08} {...HL} /></>},
  {id: 'k_nocushion', from: 251.0, to: 253.98, enter: 'cut', why: 'No cushion.',
    el: <><F src="commodity_cuba_truck.mp4" start={0} grade="bw" /><Highlight text="NO CUSHION" at={252.88} {...HL} /></>},
  {id: 'k_rail', from: 253.98, to: 257.16, enter: 'cut', why: 'Meanwhile the US built railroads.',
    el: <><F src="commodity_oil_train.mp4" start={0} grade="bw" /><Highlight text="RAILROADS" at={256.28} {...HL} /></>},
  {id: 'k_steel', from: 257.16, to: 259.02, enter: 'cut', why: 'Steel mills, oil refineries.',
    el: <><F src="commodity_steel_ladle.mp4" start={0} grade="bw" /><ListWords anchor="left" x={120} y={520} size={76} color={CREAM} dim={false} items={l('Steel mills.|Oil refineries.', [257.16, 257.96])} /></>},
  {id: 'k_market', from: 259.02, to: 262.72, enter: 'cut', why: 'A continental marketplace.',
    el: <><F src="commodity_oil_aerial.mp4" start={0} grade="warm" /><Highlight text="A CONTINENTAL MARKETPLACE" at={259.3} {...HL} /></>},

  // ================= COLD WAR =================
  {id: 'w_widened', from: 262.72, to: 265.84, enter: 'dissolve', why: 'The divide widened — Brazil 1979.',
    el: <><F src="coldwar_brazil_skyline.mp4" start={0} grade="warm" /><Highlight text="THE DIVIDE WIDENED" at={263.2} {...HL} /></>},
  {id: 'w_chess', from: 265.84, to: 269.58, enter: 'cut', why: 'Cold War chessboard: Castro and Khrushchev.',
    el: <><F src="coldwar_amigo_castro_khrushchev.mp4" start={0} grade="bw" />
      <NameStrip text="Nikita Khrushchev" sub="Soviet Union" at={266.2} x={520} y={700} rot={-2} size={34} />
      <NameStrip text="Fidel Castro" sub="Cuba" at={266.7} x={1440} y={700} rot={1.5} size={34} />
      <Highlight text="A GEOPOLITICAL CHESSBOARD" at={267.88} {...HL} /></>},
  {id: 'w_guat', from: 269.58, to: 272.58, enter: 'cut', why: '"The CIA backing coups in Guatemala in 1954" — the CIA memo of 31 March 1954, its "disposal" line marked on "backing coups".',
    el: <DocCard photo="cia_guatemala.jpg" aspect={1.7097} at={269.64} source="CIA · declassified, 31 March 1954"
      marks={[{box: [0.2021, 0.3508, 0.7344, 0.3972], at: 270.28, until: 271.6}]} />},
  {id: 'w_chile', from: 272.58, to: 274.74, enter: 'cut', why: 'Chile 1973: La Moneda burning.',
    el: <><F src="coldwar_chile_moneda_burn.mp4" start={0} grade="bw" /><DateTag text="Chile, 1973" at={273.36} x={1420} y={900} /></>},
  {id: 'w_anti', from: 274.74, to: 279.76, enter: 'cut', why: 'Tanks at La Moneda — anti-communism over democracy.',
    el: <><F src="coldwar_chile_tanks_moneda.mp4" start={0} grade="bw" /><Highlight text="ANTI-COMMUNISM" at={278.12} {...HL} /></>},
  {id: 'w_80s', from: 279.76, to: 285.36, enter: 'cut', why: 'The 1980s: the Lost Decade.',
    el: <ConcreteWall><GhostTitle text="1980s" x={960} y={420} size={300} /><Highlight text="THE LOST DECADE" at={283.86} x={960} y={720} size={84} /></ConcreteWall>},
  {id: 'w_oil', from: 285.36, to: 290.18, enter: 'cut', why: 'Loans from the oil boom.',
    el: <><F src="coldwar_us_derrick.mp4" start={0} rate={0.92} grade="bw" /><DateTag text="1970s oil boom" at={287.74} x={1400} y={900} /></>},
  {id: 'w_volcker', from: 290.18, to: 293.3, enter: 'cut', why: 'Volcker named.',
    el: <ConcreteWall><PhotoPrint src="coldwar_volcker_reagan.jpg" at={290.3} x={960} y={500} w={1100} rot={-1} from="bottom" /><NameStrip text="Paul Volcker" at={291.98} x={620} y={880} sub="Federal Reserve" /></ConcreteWall>},
  {id: 'w_inflation', from: 293.3, to: 297.18, enter: 'cut', why: '"Hyperinflation tore through Argentina, Brazil and Peru" — each country lit on its name.',
    el: <DocMap id={4} spec={{mode: 'territory', title: 'Hyperinflation', year: '1980s',
      camera: {fromCenter: [-60, -16], fromZoom: 2.0, center: [-62, -20], zoom: 2.25},
      territories: [
        {id: 'arg', name: 'ARGENTINA', color: '#9e1b1b', countries: ['Argentina'], appearAt: 294.64},
        {id: 'bra', name: 'BRAZIL', color: '#9e1b1b', countries: ['Brazil'], appearAt: 295.58},
        {id: 'peru', name: 'PERU', color: '#9e1b1b', countries: ['Peru'], appearAt: 296.26},
      ],
      regions: [
        {label: 'Argentina', coordinates: [-65.5, -36], size: 34, italic: false, appearAt: 294.64},
        {label: 'Brazil', coordinates: [-51, -10], size: 44, italic: false, appearAt: 295.58},
        {label: 'Peru', coordinates: [-76.2, -11.2], size: 30, italic: false, appearAt: 296.26},
      ]}} />},
  {id: 'w_poverty', from: 297.18, to: 301.16, enter: 'cut', why: 'Millions pushed back into poverty.',
    el: <><F src="coldwar_amigo_crowd.mp4" start={0} rate={0.88} grade="bw" /><Highlight text="MILLIONS BACK INTO POVERTY" at={299.06} {...HL} /></>},
  {id: 'w_generation', from: 301.16, to: 303.68, enter: 'cut', why: 'A generation of growth evaporated - abandoned, rusting machinery.',
    el: <><F src="north_abandoned_machinery.mp4" start={0} grade="bw" /><Highlight text="A GENERATION OF GROWTH, GONE" at={301.68} {...HL} /></>},

  // ================= TAKEAWAY =================
  {id: 't_question', from: 303.68, to: 306.3, enter: 'cut', why: 'The takeaway question.',
    el: <Black><QuoteText x={960} y={540} size={86} width={1300} color={CREAM} words={q("So what's the real takeaway?", [303.68, 304.32, 304.58, 304.7, 305.02])} mark={['takeaway?']} /></Black>},
  {id: 't_resources', from: 306.3, to: 309.34, enter: 'cut', why: 'Not resources or geography.',
    el: <><F src="colonial_peru37_machu_valley.mp4" start={0} grade="sepia" /><ListWords anchor="left" x={120} y={520} size={76} color={CREAM} dim={false} items={l('Not resources.|Not geography.', [307.56, 308.36])} /></>},
  {id: 't_rules', from: 309.34, to: 315.74, enter: 'cut', why: 'The thesis as three lines.',
    el: (
      <ConcreteWall>
        <GhostTitle text="THE RULES" x={960} y={260} size={220} />
        <ListWords x={960} y={600} size={70} color={CREAM} items={l('Who writes the rules.|Who benefits from them.|Who has skin in the game.', [309.86, 311.26, 312.8])} />
      </ConcreteWall>
    )},
  {id: 't_accident', from: 315.74, to: 318.28, enter: 'cut', why: '"Didn\'t get rich by accident."',
    el: <><F src="commodity_steel_mill.mp4" start={0} grade="bw" /><Highlight text="NOT BY ACCIDENT" at={317.3} {...HL} /></>},
  {id: 't_institutions', from: 318.28, to: 320.5, enter: 'cut', why: 'Early institutions.', el: <F src="coldwar_us_town_aerial.mp4" start={0} grade="warm" />},
  {id: 't_flawed', from: 320.5, to: 324.14, enter: 'cut', why: 'Flawed, but incentives for broad participation.',
    el: <><F src="coldwar_us_houses.mp4" start={0} grade="warm" /><Highlight text="BROAD PARTICIPATION" at={322.76} {...HL} /></>},
  {id: 't_build', from: 324.14, to: 327.38, enter: 'cut', why: 'Ordinary people build.',
    el: <><F src="north_farmer_plow.mp4" start={0} grade="bw" /><Highlight text="ORDINARY PEOPLE BUILD" at={325.52} {...HL} /></>},
  {id: 't_latam', from: 327.38, to: 330.26, enter: 'cut', why: 'Latin America didn\'t stay poor by accident either.', el: <F src="colonial_peru37_cathedral.mp4" start={0} grade="sepia" />},
  {id: 't_machine', from: 330.26, to: 336.06, enter: 'cut', why: 'An extraction machine — the cross-section of a Potosí mine.',
    el: <ConcreteWall><PhotoPrint src="ind2_potosi_4.jpg" at={330.3} x={960} y={500} w={1150} rot={1} from="fade" /><Highlight text="AN EXTRACTION MACHINE" at={331.04} x={960} y={960} size={66} /></ConcreteWall>},
  {id: 't_foundations', from: 336.06, to: 339.48, enter: 'cut', why: '"Original foundations" — literally: colonial walls on Inca stone.', el: <F src="colonial_cuzco20s_wall.mp4" start={0} grade="sepia" />},
  {id: 't_escape', from: 339.48, to: 341.9, enter: 'cut', why: 'Whether the region escapes the cycle.', el: <F src="colonial_mex_bellasartes.mp4" start={0} grade="sepia" />},
  {id: 't_100', from: 341.9, to: 345.54, enter: 'cut', why: 'The next hundred years.',
    el: <Black><BigSerif text="100" at={344.16} x={960} y={500} size={300} color={CREAM} sub="the next hundred years" /></Black>},

  // ================= OUTRO (type only) =================
  {id: 'o_coin', from: 345.54, to: 350.98, enter: 'dissolve', why: 'Call to action, type only.',
    el: <Black><QuoteText x={960} y={460} size={64} width={1400} color={CREAM} words={q('If you made it this far,', [345.54, 345.74, 345.86, 346.08, 346.18, 346.42])} /><Highlight text="DROP A SILVER COIN IN THE COMMENTS" at={347.02} x={960} y={640} size={58} /></Black>},
  {id: 'o_sub', from: 350.98, to: 356.28, enter: 'cut', why: 'Subscribe.',
    el: <Black><QuoteText x={960} y={440} size={56} width={1400} color={CREAM} words={q('Deep economic stories your thing?', [351.66, 351.88, 352.18, 352.66, 352.94])} /><Highlight text="SUBSCRIBE" at={353.84} x={960} y={640} size={90} /></Black>},
  {id: 'o_thanks', from: 356.28, to: END, enter: 'cut', why: 'Thanks for watching.',
    el: <Black><BigSerif text="Thanks for watching" at={356.28} x={960} y={520} size={110} color={CREAM} /></Black>},
];

// film burns (FilmBurn.tsx clips with their own projector sound) on the section turns, only where the picture
// changes layer (film -> print/graphic or back), never film -> film; the cut hides under the burn's white peak
export const BURNS: {at: number; n: number}[] = [
  {at: 44.98, n: 4}, // structural (film) -> conquest painting (print)
  {at: 97.66, n: 6}, // silver-road map -> NORTH card
  {at: 153.2, n: 12}, // palace (film) -> 1700 card
  {at: 216.84, n: 1}, // broken empire (print) -> commodity card
  {at: 279.76, n: 11}, // tanks at La Moneda (film) -> 1980s card
  {at: 303.68, n: 5}, // rusting machinery (film) -> takeaway question
];
export const SFX: {at: number; file: string; vol: number}[] = [];
