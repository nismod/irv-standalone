import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { numFormat, numRangeFormat, unique } from 'lib/helpers';
const padding = { px: 0.25, py: 0.25 };
export const RPDamageTable = ({ damages }) => {
  const parameterNames: string[] = unique<string>(
    damages.flatMap((damage) => Object.keys(damage.parameters)),
  );
  return (
  <TableContainer sx={{ maxHeight: 250 }} tabIndex={0}>
    <Table size="small" padding="none" stickyHeader>
      <TableHead>
        <TableRow>
          <TableCell sx={padding}>
            <abbr title="Return Period">RP</abbr>
          </TableCell>
          {parameterNames.map((name) => <TableCell sx={padding} key={name}>{name}</TableCell>)}
          <TableCell sx={padding} align="right">
            Damages (J$)
          </TableCell>
          <TableCell sx={{ pr: 0, pl: padding.px, py: padding.py }} align="right">
            Loss (J$/day)
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {damages.map((d) => (
          <TableRow key={d.key}>
            <TableCell sx={padding}>{d.rp}</TableCell>
            {parameterNames.map((name) => (
              <TableCell sx={padding} key={name}>{String(d.parameters[name] ?? '')}</TableCell>
            ))}
            <TableCell sx={padding} align="right">
              {numFormat(d.damage_mean)}
              <br />({numRangeFormat(d.damage_amin, d.damage_amax)})
            </TableCell>
            <TableCell sx={{ pr: 0, pl: padding.px, py: padding.py }} align="right">
              {d.loss_amax ? numFormat(d.loss_mean) : '-'}
              <br />
              {d.loss_amax ? `(${numRangeFormat(d.loss_amin, d.loss_amax)})` : null}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
  );
};
