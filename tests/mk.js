const XLSX = require('xlsx');
// planilha no modelo antigo do Lucas (Data, Competição, Entrada, '', Mercado, Bookies, Stake, Odd, Status)
const rows = [
  ['Planilha de apostas'], [],
  ['Data','Competição','Entrada','','Mercado','Bookies','Stake','Odd','Status'],
  [new Date(2026,9,1),'Brasileirão','Palmeiras','Internacional','Resultado Final: Palmeiras','Bet365',40,2.0,'GREEN'],
  [new Date(2026,9,1),'Brasileirão','Flamengo','Grêmio','Over 2.5','Betano',20,1.9,'RED'],
  [new Date(2026,9,2),'NBA','Lakers','Celtics','Lakers +5.5','Bet365',30,1.85,'ANULADO'],
  [new Date(2026,10,3),'Champions','Real Madrid','Man City','Ambos marcam','Pinnacle',50,1.7,'GREEN'],
];
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), 'Outubro');
XLSX.writeFile(wb, 'antiga.xlsx', {cellDates:true});
