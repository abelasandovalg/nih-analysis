import apache_beam as beam
from apache_beam.io import WriteToText
import logging

class ExtractNCTDoFn(beam.DoFn):
  # extreacts all columns from table
  def process(self, element):
     nih_record = element 
     nct_number = nih_record.get('nct_number')
     eligibility_study_pop = nih_record.get('eligibility_study_pop')
     eligibility_sampling_method = nih_record.get('eligibility_sampling_method')
     eligibility_criteria = nih_record.get('eligibility_criteria')
     eligibility_gender = nih_record.get('eligibility_gender')
     eligibility_minimum_age = nih_record.get('eligibility_minimum_age')
     eligibility_maximum_age = nih_record.get('eligibility_maximum_age')
     eligibility_healthy_volunteers = nih_record.get('eligibility_healthy_volunteers')
        
     # create key, value pairs 
     eligibility_tuple = (nct_number, nih_record) 
     return [eligibility_tuple]

class DedupEligibilityRecordsFn(beam.DoFn): 
  # removes duplicates from eligibility table 
  def process(self, element): 
     nct_number, eligibility_obj = element # eligibility_obj is an _UnwindowedValues object
     eligibility_list = list(eligibility_obj) # cast to list type 
     eligibility_record = eligibility_list[0]
     return [eligibility_record]
           
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
     sql = 'SELECT nct_number, eligibility_study_pop, eligibility_sampling_method, eligibility_criteria, eligibility_gender, eligibility_minimum_age, eligibility_maximum_age, eligibility_healthy_volunteers FROM nih_modeled.eligibility limit 10'
     bq_source = beam.io.BigQuerySource(query=sql, use_standard_sql=True)

     # query results from bigquery
     query_results = p | 'Read from BigQuery' >> beam.io.Read(bq_source)
        
     query_results | 'Write eligibility records input' >> WriteToText('input.txt')

     # p collection from eligibility table
     eligibility_pcoll = query_results | 'Extract eligibility records' >> beam.ParDo(ExtractNCTDoFn())
    
     grouped_eligibility_pcoll = eligibility_pcoll | 'Grouped eligibility records' >> beam.GroupByKey()
        
     # records sorted by nct number, duplicates removed
     distinct_eligibility_pcoll = grouped_eligibility_pcoll | 'Dedup eligibility records' >> beam.ParDo(DedupEligibilityRecordsFn()) 
        
     # write to output txt file
     distinct_eligibility_pcoll | 'Write results' >> WriteToText('output.txt')
    
     dataset_id = 'nih_modeled'
     table_id = 'eligibility_Beam'
     schema_id = 'nct_number:STRING, eligibility_study_pop:STRING, eligibility_sampling_method:STRING, eligibility_criteria:STRING, eligibility_gender:STRING, eligibility_minimum_age:STRING, eligibility_maximum_age:STRING, eligibility_healthy_volunteers:STRING'

     # write PCollection to new BQ table
     distinct_eligibility_pcoll | 'Write BQ table' >> beam.io.WriteToBigQuery(dataset=dataset_id, 
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