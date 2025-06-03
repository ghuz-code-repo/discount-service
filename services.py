import os
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import sqlite3
from dotenv import load_dotenv
from models import db, PropertyType, Complex, DiscountObject, PaymentType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ExcelDataService:
    def __init__(self, env_file_path: str = ".env", excel_path: Optional[str] = None, columns: Optional[List[str]] = None):
        """Initialize the service with configuration from environment or direct parameters."""
        # Load environment variables
        load_dotenv(env_file_path)
        
        # Get Excel file path from parameter or environment
        self.excel_file_path = excel_path or os.getenv("EXCEL_FILE_PATH")
        if not self.excel_file_path:
            raise ValueError("Excel file path not provided.")

        # Get columns from parameter or environment (comma-separated string)
        columns_str = os.getenv("EXCEL_COLUMNS")
        if columns:
            self.columns = columns
        elif columns_str:
            self.columns = [col.strip() for col in columns_str.split(',')]
        else:
            self.columns = None # Read all columns if none specified

    def get_data_from_excel(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Reads data from the Excel file.
        
        :param sheet_name: Name of the sheet to read. If None, uses EXCEL_SHEET_NAME from env.
        :return: A list of dictionaries with the Excel data.
        """
        if not os.path.exists(self.excel_file_path):
            raise FileNotFoundError(f"Excel file not found at {self.excel_file_path}")
        try:
            # Get sheet name from environment if not provided
            sheet = sheet_name or os.getenv("EXCEL_SHEET_NAME")
            
            if self.columns:
                df = pd.read_excel(self.excel_file_path, sheet_name=sheet, usecols=self.columns)
            else:
                df = pd.read_excel(self.excel_file_path, sheet_name=sheet)
            
            # Convert NaN to None for JSON compatibility
            df = df.where(pd.notnull(df), None)
            return df.to_dict(orient='records')
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")


class SQLiteDataService:
    def __init__(self, env_file_path: str = ".env", db_path: Optional[str] = None):
        """Initialize the service with the SQLite database path."""
        load_dotenv(env_file_path)
        self.db_path = db_path or os.getenv("DB_FILE_PATH")
        if not self.db_path:
            raise ValueError("SQLite database path not provided.")
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"SQLite database file not found at {self.db_path}")

    def get_data_from_sqlite(self, table_name: str, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetches data from the specified table in the SQLite database.
        
        :param table_name: Name of the table to fetch data from.
        :param columns: Optional list of column names to select. If None, selects all columns.
        :return: A list of dictionaries, where each dictionary represents a row.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()

            if columns:
                # Sanitize column names to prevent SQL injection if they are not hardcoded
                # For simplicity, assuming columns are trusted or validated elsewhere
                cols_str = ", ".join(f'"{col}"' for col in columns) # Quote column names
            else:
                cols_str = "*"
            
            # Sanitize table_name if it's dynamic, for now assuming it's safe
            query = f'SELECT {cols_str} FROM "{table_name}"' # Quote table name
            
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            # Log the exception e
            raise ValueError(f"SQLite error: {e}")
        finally:
            if conn:
                conn.close()


class DataSyncService:
    """Service to synchronize data between Excel and the database."""
    
    def __init__(self, excel_service: Optional[ExcelDataService] = None):
        """
        Initialize with an Excel data service.
        
        :param excel_service: Configured ExcelDataService instance (optional)
        """
        self.excel_service = excel_service
    
    def sync_all_data(self):
        """Synchronize all data from Excel to the database using configured ExcelDataService."""
        if not self.excel_service:
            raise ValueError("Excel service not configured for sync_all_data operation")
            
        # Get data from excel - assumes the expected columns are present
        data = self.excel_service.get_data_from_excel()
        
        # Process data through common sync pipeline
        self._process_sync_data(data)
    
    def sync_from_file(self, file_path: str, sheet_name: Optional[str] = None):
        """
        Synchronize data from a specific Excel file.
        
        :param file_path: Path to the Excel file to process
        :param sheet_name: Optional name of the sheet to read
        """
        # Create a temporary ExcelDataService with the provided file
        temp_service = ExcelDataService(excel_path=file_path)
        
        # Get data from the specified file
        data = temp_service.get_data_from_excel(sheet_name)
        
        # Process data through common sync pipeline
        self._process_sync_data(data)
        
    def sync_from_upload(self, file_object, sheet_name: Optional[str] = None):
        """
        Synchronize data from an uploaded file object (e.g., from Flask request.files).
        
        :param file_object: The uploaded file object
        :param sheet_name: Optional name of the sheet to read
        """
        try:
            # Get sheet name from environment if not provided
            sheet = sheet_name or os.getenv("EXCEL_SHEET_NAME")
            
            # Read directly from the uploaded file using pandas
            df = pd.read_excel(file_object, sheet_name=sheet)
            
            # Replace NaN values with None before converting to dict
            df = df.replace({pd.NA: None})
            data = df.to_dict(orient='records')
            
            # Process data through common sync pipeline
            self._process_sync_data(data)
        except Exception as e:
            raise ValueError(f"Error processing uploaded Excel file: {e}")
    
    def _process_sync_data(self, data: List[Dict[str, Any]]):
        """
        Common method to process and sync data regardless of source.
        
        :param data: Excel data as a list of dictionaries
        """
        # Process and sync each type of data
        self.sync_property_types(data)
        self.sync_payment_types(data)
        self.sync_complexes(data)
        self.sync_discounts(data)
        
        # Commit all changes to the database
        db.session.commit()
    
    def sync_property_types(self, data: List[Dict[str, Any]]):
        """
        Synchronize property types from Excel data.
        
        :param data: Excel data with "Тип" column
        """
        # Extract unique property types
        unique_types = set(item.get("Тип") for item in data if item.get("Тип"))
        
        # For each unique type, add if it doesn't exist
        for type_name in unique_types:
            existing_type = PropertyType.query.filter_by(name=type_name).first()
            if not existing_type:
                new_type = PropertyType(name=type_name)
                db.session.add(new_type)
    
    def sync_payment_types(self, data: List[Dict[str, Any]]):
        """
        Synchronize payment types from Excel data.
        
        :param data: Excel data with "Вид оплаты" column
        """
        # Extract unique payment types
        unique_types = set(item.get("Вид оплаты") for item in data if item.get("Вид оплаты"))
        
        # For each unique type, add if it doesn't exist
        for type_name in unique_types:
            existing_type = PaymentType.query.filter_by(name=type_name).first()
            if not existing_type:
                new_type = PaymentType(name=type_name)
                db.session.add(new_type)
    
    def sync_complexes(self, data: List[Dict[str, Any]]):
        """
        Synchronize complexes from Excel data.
        
        :param data: Excel data with "Название" column
        """
        # Extract unique complexes
        complex_names = set(item.get("Название") for item in data if item.get("Название"))
                
        # For each complex, add if it doesn't exist
        for name in complex_names:
            existing_complex = Complex.query.filter_by(name=name).first()
            if not existing_complex:
                new_complex = Complex(name=name)
                db.session.add(new_complex)
    
    def sync_discounts(self, data: List[Dict[str, Any]]):
        """Synchronize discount information."""
        for item in data:
            # Debug print raw data
            logger.debug(f"Raw Excel row data: {item}")
            
            complex_name = item.get("Название")
            property_type_name = item.get("Тип")
            payment_type_name = item.get("Вид оплаты")
            mpp_discount = item.get("Скидка МПП")  # Note exact column name match
            opt_discount = item.get("Скидка РОП")  # Note exact column name match
            
            logger.debug(f"Extracted values - MPP: {mpp_discount}, ROP: {opt_discount}")
            
            # Skip if essential data is missing
            if not all([complex_name, property_type_name, payment_type_name]):
                logger.warning(f"Missing required data: complex={complex_name}, "
                             f"type={property_type_name}, payment={payment_type_name}")
                continue
            
            # Convert discount values, handle percentage format
            try:
                # Remove any % signs and convert to float
                mpp_str = str(mpp_discount).replace('%', '').strip() if mpp_discount else '0'
                opt_str = str(opt_discount).replace('%', '').strip() if opt_discount else '0'
                
                # Convert to decimal (e.g., 5% becomes 0.05)
                mpp_disc = (float(mpp_str) * 100.0)/100.0
                opt_disc = (float(opt_str) * 100.0)/100.0
                
                logger.debug(f"Converted discounts - MPP: {mpp_disc}, ROP: {opt_disc}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting discount values: {e}")
                logger.error(f"Raw values - MPP: {mpp_discount}({type(mpp_discount)}), "
                           f"ROP: {opt_discount}({type(opt_discount)})")
                continue
            
            # Look up required objects
            complex_obj = Complex.query.filter_by(name=complex_name).first()
            prop_type = PropertyType.query.filter_by(name=property_type_name).first()
            payment_type = PaymentType.query.filter_by(name=payment_type_name).first()
            
            if not all([complex_obj, prop_type, payment_type]):
                logger.warning("Could not find all required database objects")
                continue
            
            # Get or create discount object
            discount_obj = DiscountObject.query.filter_by(
                complex_id=complex_obj.id,
                type_id=prop_type.id,
                payment_type_id=payment_type.id
            ).first()
            
            if discount_obj:
                discount_obj.mpp_discount = mpp_disc
                discount_obj.opt_discount = opt_disc
                logger.debug(f"Updated discount object {discount_obj.id} with "
                           f"MPP: {mpp_disc}, ROP: {opt_disc}")
            else:
                discount_obj = DiscountObject(
                    complex_id=complex_obj.id,
                    type_id=prop_type.id,
                    payment_type_id=payment_type.id,
                    mpp_discount=mpp_disc,
                    opt_discount=opt_disc
                )
                db.session.add(discount_obj)
                logger.debug("Created new discount object")