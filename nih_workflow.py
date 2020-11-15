import datetime
from airflow import models
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator

default_dag_args = {
    'start_date': datetime.datetime(2020, 5, 3)
}

staging_dataset = 'nih_workflow_staging'
modeled_dataset = 'nih_workflow_modeled'

bq_query_start = 'bq query --use_legacy_sql=false '

create_arm_groups_sql = 'create or replace table ' + modeled_dataset + '''.arm_groups as
                      select nct_number, arm_group_label, arm_group_type, description, serialid
                      from ''' + staging_dataset + '.arm_groups'

create_clinical_results_sql = 'create or replace table ' + modeled_dataset + '''.clinical_results as
                    select nct_number, type, title, time_frame, safety_issue, results_population, serialid
                    from ''' + staging_dataset + '.clinical_results'

create_clinical_studies_main_sql = 'create or replace table ' + modeled_dataset + '''.clinical_studies_main as
                    select nct_number, org_study_id, secondary_id, official_title, brief_summary, overall_status, enrollment, enrollment_type, CAST(start_date AS DATE) AS start_date, CAST(completion_date AS DATE) AS completion_date, condition, number_of_arms, number_of_groups, phase, study_type, study_design, CAST(first_received_date AS DATE) AS first_received_date, CAST(verification_date AS DATE) AS verification_date, lead_sponsor_agency, lead_sponsor_agency_class, overall_official_last_name AS official_full_name, overall_official_affiliation, serialid
                    from ''' + staging_dataset + '.clinical_studies_main'

create_collaborators_sql = 'create or replace table ' + modeled_dataset + '''.collaborators as
                      select  nct_number, collaborator_agency, collaborator_agency_class, serialid
                      from ''' + staging_dataset + '.collaborators'

create_contacts_sql = 'create or replace table ' + modeled_dataset + '''.contacts as
                    select nct_number, last_name, phone, phone_ext, email, serialid
                    from ''' + staging_dataset + '.contacts'

create_eligibility_sql = 'create or replace table ' + modeled_dataset + '''.eligibility as
                      select nct_number, eligibility_study_pop, eligibility_sampling_method, eligibility_criteria, eligibility_gender, eligibility_minimum_age, eligibility_maximum_age, eligibility_healthy_volunteers 
                      from ''' + staging_dataset + '.clinical_studies_main'

create_interventions_sql = 'create or replace table ' + modeled_dataset + '''.interventions as
                      select nct_number, intervention_type, intervention_name, arm_group_label, serialid
                      from ''' + staging_dataset + '.interventions'

create_locations_sql = 'create or replace table ' + modeled_dataset + '''.locations as
                    select nct_number, facility_name, facility_city, facility_state, facility_zip, facility_country, serialid
                    from ''' + staging_dataset + '.locations'

create_primary_outcomes_sql = 'create or replace table ' + modeled_dataset + '''.primary_outcomes as
                      select nct_number, measure, time_frame, safety_issue, description, serialid
                      from ''' + staging_dataset + '.primary_outcomes'

create_secondary_outcomes_sql = 'create or replace table ' + modeled_dataset + '''.secondary_outcomes as
                    select nct_number, measure, time_frame, safety_issue, description, serialid
                    from ''' + staging_dataset + '.secondary_outcomes'

create_other_outcomes_sql = 'create or replace table ' + modeled_dataset + '''.other_outcomes as
                    select nct_number, measure, time_frame, safety_issue, outcome_description as description, serialid
                    from ''' + staging_dataset + '.other_outcomes'

create_responsible_parties_sql = 'create or replace table ' + modeled_dataset + '''.responsible_parties as
                      select nct_number,name_title, organization, type, investigator_affiliation, investigator_full_name, investigator_title, serialid
                      from ''' + staging_dataset + '.responsible_parties'

create_birds_eye_sql = 'create or replace table ' + modeled_dataset + '''.birds_eye as
                    select nct_number, sponsor, title, start_year, start_month, phase, condition
                    from ''' + staging_dataset + '.birds_eye'

with models.DAG(
        'nih_workflow',
        schedule_interval=None,
        default_args=default_dag_args) as dag:

    # create datasets 
    create_staging = BashOperator(
            task_id='create_staging',
            bash_command='bq --location=US mk --dataset ' + staging_dataset)
    
    create_modeled = BashOperator(
            task_id='create_modeled',
            bash_command='bq --location=US mk --dataset ' + modeled_dataset)
    
    # load tables 
    load_arm_groups = BashOperator(
            task_id='load_arm_groups',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.arm_groups \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-ArmGroups.csv"',
            trigger_rule='one_success')
    
    load_clinical_results = BashOperator(
            task_id='load_clinical_results',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.clinical_results \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-ClinicalResults.csv"',
            trigger_rule='one_success')
    
    load_clinical_studies_main = BashOperator(
            task_id='load_clinical_studies_main',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.clinical_studies_main \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-ClinicalStudiesMain.csv"',
            trigger_rule='one_success')
    
    load_collaborators = BashOperator(
            task_id='load_collaborators',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.collaborators \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-Collaborators.csv"',
            trigger_rule='one_success')
    
    load_contacts = BashOperator(
            task_id='load_contacts',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.contacts \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-Contacts.csv"',
            trigger_rule='one_success')
    
    load_interventions = BashOperator(
            task_id='load_interventions',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.interventions \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-Interventions.csv"',
            trigger_rule='one_success')
    
    load_locations = BashOperator(
            task_id='load_locations',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.locations \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-Locations.csv"',
            trigger_rule='one_success')
    
    load_primary_outcomes = BashOperator(
            task_id='load_primary_outcomes',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.primary_outcomes \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-PrimaryOutcomes.csv"',
            trigger_rule='one_success')
    
    load_secondary_outcomes = BashOperator(
            task_id='load_secondary_outcomes',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.secondary_outcomes \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-SecondaryOutcomes.csv"',
            trigger_rule='one_success')
    
    load_other_outcomes = BashOperator(
            task_id='load_other_outcomes',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.other_outcomes \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-OtherOutcomes.csv"',
            trigger_rule='one_success')
    
    load_responsible_parties = BashOperator(
            task_id='load_responsible_parties',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.responsible_parties \
                         "gs://clinical_trials_ncl/Clinical Trials/NIHClinicalTrials-ResponsibleParties.csv"',
            trigger_rule='one_success')
    
    load_birds_eye = BashOperator(
            task_id='load_birds_eye',
            bash_command='bq --location=US load --autodetect --skip_leading_rows=1 \
                         --source_format=CSV ' + staging_dataset + '.birds_eye \
                         "gs://areo-data/AERO-BirdsEye-Data.csv"',
            trigger_rule='one_success')
    
    # dummy operators 
    branch = DummyOperator(
            task_id='branch',
            trigger_rule='all_done')
    
    join = DummyOperator(
            task_id='join',
            trigger_rule='all_done')
    
    # create tables
    create_arm_groups = BashOperator(
            task_id='create_arm_groups',
            bash_command=bq_query_start + "'" + create_arm_groups_sql + "'", 
            trigger_rule='one_success')
    
    create_clinical_results = BashOperator(
            task_id='create_clinical_results',
            bash_command=bq_query_start + "'" + create_clinical_results_sql + "'", 
            trigger_rule='one_success')
    
    create_clinical_studies_main = BashOperator(
            task_id='create_clinical_studies_main',
            bash_command=bq_query_start + "'" + create_clinical_studies_main_sql + "'", 
            trigger_rule='one_success')
        
    create_collaborators = BashOperator(
            task_id='create_collaborators',
            bash_command=bq_query_start + "'" + create_collaborators_sql + "'", 
            trigger_rule='one_success')
           
    create_contacts = BashOperator(
            task_id='create_contacts',
            bash_command=bq_query_start + "'" + create_contacts_sql + "'", 
            trigger_rule='one_success')
    
    create_eligibility = BashOperator(
            task_id='create_eligibility',
            bash_command=bq_query_start + "'" + create_eligibility_sql + "'", 
            trigger_rule='one_success')
    
    create_interventions = BashOperator(
            task_id='create_interventions',
            bash_command=bq_query_start + "'" + create_interventions_sql + "'", 
            trigger_rule='one_success')
        
    create_locations = BashOperator(
            task_id='create_locations',
            bash_command=bq_query_start + "'" + create_locations_sql + "'", 
            trigger_rule='one_success')
           
    create_primary_outcomes = BashOperator(
            task_id='create_primary_outcomes',
            bash_command=bq_query_start + "'" + create_primary_outcomes_sql + "'", 
            trigger_rule='one_success')
    
    create_secondary_outcomes = BashOperator(
            task_id='create_secondary_outcomes',
            bash_command=bq_query_start + "'" + create_secondary_outcomes_sql + "'", 
            trigger_rule='one_success')
    
    create_other_outcomes = BashOperator(
            task_id='create_other_outcomes',
            bash_command=bq_query_start + "'" + create_other_outcomes_sql + "'", 
            trigger_rule='one_success')
        
    create_responsible_parties = BashOperator(
            task_id='create_responsible_parties',
            bash_command=bq_query_start + "'" + create_responsible_parties_sql + "'", 
            trigger_rule='one_success')
           
    create_birds_eye = BashOperator(
            task_id='create_birds_eye',
            bash_command=bq_query_start + "'" + create_birds_eye_sql + "'", 
            trigger_rule='one_success')
    
    # dataflow 
    arm_groups = BashOperator(
            task_id='arm_groups',
            bash_command='python /home/jupyter/airflow/dags/arm_groups_beam_dataflow.py')
    
    clinical_results = BashOperator(
            task_id='clinical_results',
            bash_command='python /home/jupyter/airflow/dags/clinical_results_beam_dataflow.py')
    
    clinical_studies_main = BashOperator(
            task_id='clinical_studies_main',
            bash_command='python /home/jupyter/airflow/dags/clinical_studies_main_beam_dataflow.py')
    
    collaborators = BashOperator(
            task_id='collaborators',
            bash_command='python /home/jupyter/airflow/dags/collaborators_beam_dataflow.py')
    
    contacts = BashOperator(
            task_id='contacts',
            bash_command='python /home/jupyter/airflow/dags/contacts_beam_dataflow.py')
    
    eligibility = BashOperator(
            task_id='eligibility',
            bash_command='python /home/jupyter/airflow/dags/eligibility_beam_dataflow.py')
    
    interventions = BashOperator(
            task_id='interventions',
            bash_command='python /home/jupyter/airflow/dags/interventions_beam_dataflow.py')
    
    locations = BashOperator(
            task_id='locations',
            bash_command='python /home/jupyter/airflow/dags/locations_beam_dataflow.py')
    
    primary_outcomes = BashOperator(
            task_id='primary_outcomes',
            bash_command='python /home/jupyter/airflow/dags/primary_outcomes_beam_dataflow.py')
    
    secondary_outcomes = BashOperator(
            task_id='secondary_outcomes',
            bash_command='python /home/jupyter/airflow/dags/secondary_outcomes_beam_dataflow.py')
    
    other_outcomes = BashOperator(
            task_id='other_outcomes',
            bash_command='python /home/jupyter/airflow/dags/other_outcomes_beam_dataflow.py')
    
    responsible_parties = BashOperator(
            task_id='responsible_parties',
            bash_command='python /home/jupyter/airflow/dags/responsible_parties_beam_dataflow.py')
    
    birds_eye = BashOperator(
            task_id='birds_eye',
            bash_command='python /home/jupyter/airflow/dags/birds_eye_beam_dataflow.py')
        
    create_staging >> create_modeled >> branch
    branch >> load_arm_groups >> create_arm_groups >> arm_groups
    branch >> load_clinical_results >> create_clinical_results >> clinical_results
    branch >> load_clinical_studies_main >> create_clinical_studies_main >> create_eligibility >> [clinical_studies_main, eligibility]
    branch >> load_collaborators >> create_collaborators >> collaborators
    branch >> load_contacts >> create_contacts >> contacts
    branch >> load_interventions >> create_interventions >> interventions
    branch >> load_locations >> create_locations >> locations
    branch >> load_primary_outcomes >> create_primary_outcomes >> primary_outcomes
    branch >> load_secondary_outcomes >> create_secondary_outcomes >> secondary_outcomes
    branch >> load_other_outcomes >> create_other_outcomes >> other_outcomes
    branch >> load_responsible_parties >> create_responsible_parties >> responsible_parties
    branch >> load_birds_eye >> create_birds_eye >> birds_eye