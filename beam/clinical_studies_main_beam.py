import apache_beam as beam
from apache_beam.io import WriteToText
import logging

class ExtractNCTDoFn(beam.DoFn):
  # extreacts all columns from table
  def process(self, element):
     nih_record = element 
     nct_number = nih_record.get('nct_number')
     org_study_id = nih_record.get('org_study_id')
     secondary_id = nih_record.get('secondary_id')
     official_title = nih_record.get('official_title')
     brief_summary = nih_record.get('brief_summary')
     overall_status = nih_record.get('overall_status')
     enrollment = nih_record.get('enrollment')
     enrollment_type = nih_record.get('enrollment_type')
     start_date = nih_record.get('start_date')
     completion_date = nih_record.get('completion_date')
     condition = nih_record.get('condition')
     number_of_arms = nih_record.get('number_of_arms')
     number_of_groups = nih_record.get('number_of_groups')
     phase = nih_record.get('phase')
     study_type = nih_record.get('study_type')
     study_design = nih_record.get('study_design')
     first_recieved_date = nih_record.get('first_recieved_date')
     verification_date = nih_record.get('verification_date')
     lead_sponsor_agency = nih_record.get('lead_sponsor_agency')
     lead_sponsor_agency_class = nih_record.get('lead_sponsor_agency_class')
     official_full_name = nih_record.get('official_full_name')
     overall_official_affiliation = nih_record.get('overall_official_affiliation')
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
     sql = 'SELECT nct_number, org_study_id, secondary_id, official_title, brief_summary, overall_status, enrollment, enrollment_type, start_date, competion_date, condition, number_of_arms, number_of_groups, phase, study_type, study_design, first_recieved_date, verification_date, lead_sponsor_agency, lead_sponsor_agency_class, official_full_name, overall_official_affiliation, serialid FROM nih_modeled.clinical_studies_main limit 10'
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
     table_id = 'clinical_studies_main_Beam'
     schema_id = 'nct_number:STRING, org_study_id:STRING, secondary_id:STRING, official_title:STRING, brief_summary:STRING, overall_status:STRING, enrollment:INTEGER, enrollment_type:STRING, start_date:DATE, competion_date:DATE, condition:STRING, number_of_arms:INTEGER, number_of_groups:INTEGER, phase:STRING, study_type:STRING, study_design:STRING, first_recieved_date:DATE, verification_date:DATE, lead_sponsor_agency:STRING, lead_sponsor_agency_class:STRING, official_full_name:STRING, overall_official_affiliation:STRING, serialid:INTEGER'

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