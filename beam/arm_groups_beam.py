import apache_beam as beam
from apache_beam.io import WriteToText
import logging

class ExtractNCTDoFn(beam.DoFn):
  # extreacts all columns from table
  def process(self, element):
     nih_record = element 
     nct_number = nih_record.get('nct_number')
     arm_group_label = nih_record.get('arm_group_label')
     arm_group_type = nih_record.get('arm_group_type')
     description = nih_record.get('description')
     serialid = nih_record.get('serialid')
        
     # create key, value pairs 
     kv_tuple = (nct_number, nih_record) 
     return [kv_tuple]

class DedupRecordsFn(beam.DoFn): 
  # removes duplicates from table 
  def process(self, element): 
     nct_number, table_obj = element # _UnwindowedValues object
     table_list = list(table_obj) # cast to list type 
     table_record = table_list[0]
     return [table_record]
           
def run():
     PROJECT_ID = 'probable-pager-266720'

     # project ID used by the BQ source 
     options = {
     'project': PROJECT_ID
     }
     opts = beam.pipeline.PipelineOptions(flags=[], **options)

     # create beam pipeline using local runner 
     p = beam.Pipeline('DirectRunner', options=opts)
    
     # sql code 
     sql = 'SELECT nct_number, arm_group_label, arm_group_type, description, serialid FROM nih_modeled.arm_groups limit 10'
     bq_source = beam.io.BigQuerySource(query=sql, use_standard_sql=True)

     # query results from bigquery
     query_results = p | 'Read from BigQuery' >> beam.io.Read(bq_source)
        
     query_results | 'Write records input' >> WriteToText('input.txt')

     # p collection from table
     table_pcoll = query_results | 'Extract records' >> beam.ParDo(ExtractNCTDoFn())
    
     grouped_table_pcoll = table_pcoll | 'Grouped records' >> beam.GroupByKey()
        
     # records sorted by nct number, duplicates removed
     distinct_table_pcoll = grouped_table_pcoll | 'Dedup records' >> beam.ParDo(DedupRecordsFn()) 
        
     # write to output txt file
     distinct_table_pcoll | 'Write results' >> WriteToText('output.txt')
    
     dataset_id = 'nih_modeled'
     table_id = 'arm_groups_Beam'
     schema_id = 'nct_number:STRING, arm_group_label:STRING, arm_group_type:STRING, description:STRING, serialid:INTEGER'

     # write PCollection to new BQ table
     distinct_table_pcoll | 'Write BQ table' >> beam.io.WriteToBigQuery(dataset=dataset_id, 
                                                  table=table_id, 
                                                  schema=schema_id,
                                                  project=PROJECT_ID,
                                                  create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                                                  write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                                                  batch_size=int(100))
    
     result = p.run()
     result.wait_until_finish() 

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()