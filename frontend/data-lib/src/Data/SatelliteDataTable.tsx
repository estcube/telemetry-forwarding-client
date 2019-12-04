import React from 'react';
import { createStyles, Theme, withStyles } from '@material-ui/core/styles';
import { Paper, Table, TableBody, Typography } from '@material-ui/core';
import { WithStyles } from '@material-ui/styles';
import CustomChartDataSelector from './SatelliteDataSelectionComponents/CustomChartDataSelector';
import SatelliteDataTableRows from './SatelliteDataTableComponents/SatelliteDataTableRows';

const styles = (theme: Theme) =>
  createStyles({
    root: {
      width: '100%'
    },
    paper: {
      width: 'auto',
      overflowX: 'auto',
      margin: theme.spacing(3, 2, 2, 2),
      border: 'solid',
      borderWidth: 0.5
    },
    tableTitle: {
      textAlign: 'center'
    },
    table: {
      width: '100%'
    }
  });

interface SatelliteDataTableProps extends WithStyles<typeof styles> {
  decodedPackets: { [key: string]: { [key: string]: any }[] };
  telemetryConfiguration: { [key: string]: { [key: string]: any }[] };
}

type SatelliteDataTableState = {
  allTimestamps: string[];
  tableData: { [key: string]: { [key: string]: any }[] };
  verticalTableHeaders: string[];
  combinedVerticalTableData: { [key: string]: string[] };
  toDate: string;
  fromDate: string;
  entriesPerTable: number;
  headersWithUnits: { [key: string]: string };
};

/**
 * Component for showing data tables.
 * Takes data and configuration as props, combines them and displays as a table.
 */
class SatelliteDataTable extends React.Component<SatelliteDataTableProps, SatelliteDataTableState> {
  constructor(props: SatelliteDataTableProps) {
    super(props);
    const now = new Date();
    const anotherDate = new Date();
    anotherDate.setDate(anotherDate.getDate() - 1);
    this.state = {
      combinedVerticalTableData: {},
      allTimestamps: [],
      tableData: {},
      verticalTableHeaders: [],
      toDate: now.toISOString(),
      fromDate: anotherDate.toISOString(),
      entriesPerTable: 20,
      headersWithUnits: {}
    };
  }

  componentDidMount(): void {
    this.makeCorrectDataForTables();
    this.getVerticalHeaders();
  }

  componentDidUpdate(prevProps: Readonly<SatelliteDataTableProps>, prevState: Readonly<SatelliteDataTableState>): void {
    const { tableData, fromDate, toDate, entriesPerTable } = this.state;
    if (
      (prevState.tableData !== tableData && tableData) ||
      fromDate !== prevState.fromDate ||
      toDate !== prevState.toDate ||
      entriesPerTable !== prevState.entriesPerTable
    ) {
      this.combineHeadersWithData();
    }
    const { decodedPackets } = this.props;
    if (prevProps.decodedPackets !== decodedPackets) {
      this.makeCorrectDataForTables();
      this.getVerticalHeaders();
    }
  }

  getVerticalHeaders() {
    const { telemetryConfiguration } = this.props;
    const units: { [key: string]: string } = {};
    const headers = telemetryConfiguration.fields.map(field => {
      units[field.label] = field.unit;
      return field.label;
    });
    headers.unshift('Timestamp');
    this.setState({ verticalTableHeaders: headers, headersWithUnits: units });
    return headers;
  }

  combineHeadersWithData() {
    const { tableData, allTimestamps, entriesPerTable, toDate, fromDate } = this.state;
    const verticalTableHeaders = this.getVerticalHeaders();
    const allTimestampsShort = allTimestamps
      .filter(timestamp => timestamp >= fromDate && timestamp <= toDate)
      .slice(0, entriesPerTable);
    const combinedTableData: { [key: string]: any[] } = {};
    verticalTableHeaders.forEach(tableTitle => {
      combinedTableData[tableTitle] = allTimestampsShort.map(page => {
        if (tableTitle === 'Timestamp') {
          return page;
        }
        const someValues = tableData[page].filter(dataFromOneTimestamp => {
          return dataFromOneTimestamp.label === tableTitle;
        });
        return someValues.map(someValue => {
          if (someValue.type === 'enum') {
            return someValue.values[parseInt(someValue.value, 10)];
          }
          return someValue.value;
        });
      });
    });
    const newCombinedData: { [key: string]: string[] } = {};
    Object.keys(combinedTableData).forEach(key => {
      newCombinedData[key] = combinedTableData[key].map(element => {
        if (typeof element === 'string') {
          return element;
        }
        if (element[0]) {
          return element[0];
        }
        return '';
      });
    });
    this.setState({ combinedVerticalTableData: newCombinedData });
  }

  /**
   * Combines fields from configuration with fields from data. Sets allTimestamps state.
   */
  makeCorrectDataForTables() {
    const { decodedPackets } = this.props;
    const telemetryPacketsArray = decodedPackets.packets;
    let allTimestamps: string[] = [];
    const telemetryPacketTableData: { [key: string]: any } = {};
    telemetryPacketsArray.forEach(packet => {
      allTimestamps.push(packet.packet_timestamp);
      const dataFields = packet.fields;
      const elements: any[] = [];
      Object.keys(dataFields).forEach(dataFieldKey => {
        const confElemToMatchData = this.dataKeyInConf(dataFieldKey);
        if (Object.keys(confElemToMatchData).length > 0) {
          const dataObjectProperty: { [key: string]: any } = {};
          Object.keys(confElemToMatchData).forEach(confElemKey => {
            dataObjectProperty[confElemKey] = confElemToMatchData[confElemKey];
          });
          dataObjectProperty.value = dataFields[dataFieldKey];
          elements.push(dataObjectProperty);
        }
      });
      telemetryPacketTableData[packet.packet_timestamp] = elements;
    });
    allTimestamps = allTimestamps.sort((a, b) => {
      if (a < b) return 1;
      if (a > b) return -1;
      return 0;
    });
    if (allTimestamps.length > 0) {
      this.setState({
        tableData: telemetryPacketTableData,
        allTimestamps
      });
    }
    const keys = Object.keys(telemetryPacketTableData);
    if (keys.length > 0) {
      const fromDate = new Date(keys[keys.length - 1]);
      fromDate.setDate(fromDate.getDate() - 1);
      this.setState({
        fromDate: fromDate.toISOString()
      });
    }
  }

  /**
   * Checks if data parameter is defined in configuration.
   * @param key - id of parameter top check
   */
  dataKeyInConf(key: string): { [key: string]: any } {
    const { telemetryConfiguration } = this.props;
    let correctField = null;
    telemetryConfiguration.fields.forEach(field => {
      if (field.id === key) {
        correctField = field;
      }
    });
    return correctField || {};
  }

  handleDataSelectionChange(toDate: string, fromDate: string, maxSelection: number) {
    this.setState({ toDate, fromDate, entriesPerTable: maxSelection });
  }

  render() {
    const { classes } = this.props;
    const {
      headersWithUnits,
      verticalTableHeaders,
      combinedVerticalTableData,
      fromDate,
      toDate,
      entriesPerTable
    } = this.state;
    return (
      <div className={classes.root}>
        <Typography className={classes.tableTitle} variant="h6">
          Decoded Data
          <br />
          <CustomChartDataSelector
            changeHandler={(toDates: string, fromDates: string, maxSelections: number) =>
              this.handleDataSelectionChange(toDates, fromDates, maxSelections)
            }
            fromDate={fromDate}
            toDate={toDate}
            maxEntriesPerGraph={entriesPerTable}
          />
        </Typography>
        <Paper className={classes.paper}>
          <Table size="small" padding="none" stickyHeader>
            <TableBody>
              <SatelliteDataTableRows
                entriesPerTable={entriesPerTable}
                toDate={toDate}
                fromDate={fromDate}
                combinedVerticalTableData={combinedVerticalTableData}
                verticalTableHeaders={verticalTableHeaders}
                headersWithUnits={headersWithUnits}
              />
            </TableBody>
          </Table>
        </Paper>
      </div>
    );
  }
}

export default withStyles(styles)(SatelliteDataTable);
