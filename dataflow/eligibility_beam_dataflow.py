import datetime, logging
import apache_beam as beam
from apache_beam.io import WriteToText
from apache_beam.pipeline import PipelineOptions
from apache_beam.pipeline import Pipeline
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import StandardOptions

class ExtractNCTDoFn(beam.DoFn):
  # extracts all columns from table
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
     table_tuple = (nct_number, nih_record) 
     return [table_tuple]

class DedupRecordsFn(beam.DoFn): 
  # removes duplicates from table 
  def process(self, element): 
     nct_number, table_obj = element # table_obj is an _UnwindowedValues object
     table_list = list(table_obj) # cast to list type 
     table_record = table_list[0]
     return [table_record]

def run():
     PROJECT_ID = 'probable-pager-266720'
     BUCKET = 'gs://ncorona-lyme-ncl'
     DIR_PATH = BUCKET + '/output/' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '/'

     # Create and set your PipelineOptions.
     options = PipelineOptions(flags=None)
    
     # For Dataflow execution, set the project, job_name,
     # staging location, temp_location and specify DataflowRunner.
     google_cloud_options = options.view_as(GoogleCloudOptions)
     google_cloud_options.project = PROJECT_ID
     google_cloud_options.job_name = 'eligibility-df'
     google_cloud_options.staging_location = BUCKET + '/staging'
     google_cloud_options.temp_location = BUCKET + '/temp'
     options.view_as(StandardOptions).runner = 'DataflowRunner'

     # create the Pipeline with the specified options 
     p = Pipeline(options=options)
    
     # sql code 
     sql = 'SELECT nct_number, eligibility_study_pop, eligibility_sampling_method, eligibility_criteria, eligibility_gender, eligibility_minimum_age, eligibility_maximum_age, eligibility_healthy_volunteers FROM nih_modeled.eligibility'
     bq_source = beam.io.BigQuerySource(query=sql, use_standard_sql=True)

     # query results from bigquery
     query_results = p | 'Read from BigQuery' >> beam.io.Read(bq_source)
        
     # write query results to input text file 
     query_results | 'Write records input' >> WriteToText('input.txt')

     # create p collection from  table
     table_pcoll = query_results | 'Extract table records' >> beam.ParDo(ExtractNCTDoFn())
    
     # group records by nct_number
     grouped_table_pcoll = table_pcoll | 'Grouped table records' >> beam.GroupByKey()
        
     # remove duplicate records
     distinct_table_pcoll = grouped_table_pcoll | 'Dedup table records' >> beam.ParDo(DedupRecordsFn()) 
        
     # write records to output text file 
     distinct_table_pcoll | 'Write results' >> WriteToText('output.txt')
    
     dataset_id = 'nih_modeled'
     table_id = 'eligibility_Beam_DF'
     schema_id = 'nct_number:STRING, eligibility_study_pop:STRING, eligibility_sampling_method:STRING, eligibility_criteria:STRING, eligibility_gender:STRING, eligibility_minimum_age:STRING, eligibility_maximum_age:STRING, eligibility_healthy_volunteers:STRING'

     # write PCollection to new BQ table
     distinct_table_pcoll | 'Write BQ table' >> beam.io.WriteToBigQuery(dataset=dataset_id, 
                                                  table=table_id, 
                                                  schema=schema_id,
                                                  project=PROJECT_ID,
                                                  create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                                                  write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE)
        
     result = p.run()
     result.wait_until_finish() 

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()