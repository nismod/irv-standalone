import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { numFormat, numRangeFormat, unique } from 'lib/helpers';
const padding = { px: 0.25, py: 0.25 };
export const DamageTable = ({ damages }) => {
  const parameterNames: string[] = unique<string>(
    damages.flatMap((damage) => Object.keys(damage.parameters)),
  );
  return (
  <TableContainer sx={{ maxHeight: 260 }} tabIndex={0}>
    <Table size="small" padding="none" stickyHeader>
      <TableHead>
        <TableRow>
          {parameterNames.map((name) => <TableCell sx={padding} key={name}>{name}</TableCell>)}
          <TableCell sx={padding} align="right">
            <abbr title="Expected Annual Damages">EAD (J$)</abbr>
          </TableCell>
          <TableCell sx={{ pr: 0, pl: padding.px, py: padding.py }} align="right">
            <abbr title="Expected Annual Economic Losses">EAEL</abbr> (J$/day)
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {damages.map(
          ({ key, parameters, ead_mean, ead_amin, ead_amax, eael_mean, eael_amin, eael_amax }) => (
            <TableRow key={key}>
              {parameterNames.map((name) => (
                <TableCell sx={padding} key={name}>{String(parameters[name] ?? '')}</TableCell>
              ))}
              <TableCell sx={padding} align="right">
                {numFormat(ead_mean)}
                <br />({numRangeFormat(ead_amin, ead_amax)})
              </TableCell>
              <TableCell sx={{ pr: 0, pl: padding.px, py: padding.py }} align="right">
                {eael_amax ? numFormat(eael_mean) : '-'}
                <br />
                {eael_amax ? `(${numRangeFormat(eael_amin, eael_amax)})` : null}
              </TableCell>
            </TableRow>
          ),
        )}
      </TableBody>
    </Table>
  </TableContainer>
  );
};
